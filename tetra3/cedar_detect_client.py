# Copyright (c) 2024 Steven Rosenthal smr@dt3.org
# See LICENSE file in root directory for license terms.

from __future__ import annotations
import logging
import subprocess
import time
from pathlib import Path
from typing import Union

import grpc
from multiprocessing import shared_memory
import numpy as np

from tetra3 import cedar_detect_pb2, cedar_detect_pb2_grpc

_bin_dir = Path(__file__).parent / "bin"


class CedarDetectClient:
    """Executes the cedar-detect-server binary as a subprocess. That binary is a
    gRPC server described by the tetra3/proto/cedar_detect.proto file.
    """

    def __init__(self, logger = None, binary_path: Union[Path, str, None] = None, port=50051):
        """Spawns the cedar-detect-server subprocess.

        Args:
            logger: If have a logger object, pass it in here. Otherwise one will be created
                locally.
            binary_path: If you wish to specify a custom location for the `cedar-detect-server` binary you
                may do so, otherwise the default is to search in the relative directory "./bin"
            port: Customize the `cedar-detect-server` port if running multiple instances.
        """
        if logger is None:
            self._logger = logging.getLogger('CedarDetectClient')
            # Add new handlers to the logger.
            self._logger.setLevel(logging.DEBUG)
            # Console handler at INFO level
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(
                logging.Formatter('%(asctime)s:%(name)s-%(levelname)s: %(message)s'))
            self._logger.addHandler(ch)
        else:
            self._logger = logger
        self._binary_path: Path = Path(binary_path) if binary_path else _bin_dir / "cedar-detect-server"
        if not self._binary_path.exists() or not self._binary_path.is_file():
            raise ValueError(f"The cedar-detect-server binary could not be found at '{self._binary_path}'.")
        self._port = port

        self._subprocess = subprocess.Popen([self._binary_path, '--port', str(self._port)])
        # Will initialize on first use.
        self._stub = None
        self._shmem = None
        self._shmem_size = 0
        # Try shared memory, fall back if an error occurs.
        self._use_shmem = True

    def __del__(self):
        self._subprocess.kill()
        self._del_shmem()

    def _get_stub(self):
        if self._stub is None:
            channel = grpc.insecure_channel('localhost:%d' % self._port)
            self._stub = cedar_detect_pb2_grpc.CedarDetectStub(channel)
        return self._stub

    # Returns True if the shared memory file was re-created with a new size.
    def _alloc_shmem(self, size):
        resized = False
        if self._shmem is not None and size > self._shmem_size:
            self._shmem.close()
            self._shmem.unlink()
            self._shmem = None
            resized = True
        if self._shmem is None:
            self._shmem = shared_memory.SharedMemory(
                "/cedar_detect_image", create=True, size=size)
            self._shmem_size = size
        return resized

    def _del_shmem(self):
        if self._shmem is not None:
            self._shmem.close()
            self._shmem.unlink()
            self._shmem = None

    def extract_centroids(self, image, sigma, use_binned, binning=None,
                          detect_hot_pixels=True, normalize_rows=True):
        """Invokes the CedarDetect.ExtractCentroids() RPC. Returns [(y,x)] of the
        detected star centroids.
        """
        np_image = np.asarray(image, dtype=np.uint8)
        (height, width) = np_image.shape

        centroids_result = None
        im = None
        rpc_exception = None
        retried = False
        while True:
            if rpc_exception is not None:
                # See if subprocess exited. If so, we restart it and retry once.
                returncode = self._subprocess.poll()
                if returncode is None:
                    # Subprocess still there; just propagate the exception.
                    raise rpc_exception
                self._logger.error('Subprocess exit code: %s' % returncode)
                if retried:
                    # We already retried once, bail.
                    raise rpc_exception
                retried = True
                rpc_exception = None
                self._logger.error('Creating new subprocess')
                self._subprocess = subprocess.Popen(
                    [self._binary_path, '--port', str(self._port)])
                self._stub = None

            if self._use_shmem:
                # Use shared memory to make the gRPC calls faster. This works only
                # when the client (this program) and the CedarDetect gRPC server are
                # running on the same machine.

                # The image data is passed in a shared memory object, with the gRPC
                # request giving the name of the shared memory object.
                resized = self._alloc_shmem(size=width*height)
                # Create numpy array backed by shmem.
                shimg = np.ndarray(np_image.shape, dtype=np_image.dtype, buffer=self._shmem.buf)
                # Copy np_image into shimg. This is much cheaper than passing image
                # over the gRPC call.
                shimg[:] = np_image[:]

                im = cedar_detect_pb2.Image(width=width, height=height,
                                            shmem_name=self._shmem.name, reopen_shmem=resized)
                req = cedar_detect_pb2.CentroidsRequest(
                    input_image=im, sigma=sigma, return_binned=False,
                    binning=binning, use_binned_for_star_candidates=use_binned,
                    detect_hot_pixels=detect_hot_pixels, normalize_rows=normalize_rows)
                try:
                    centroids_result = self._get_stub().ExtractCentroids(req,
                                                                         wait_for_ready=True,
                                                                         timeout=2)
                    break  # Succeeded, break out of retry loop.
                except grpc.RpcError as err:
                    if err.code() == grpc.StatusCode.INTERNAL:
                        self._logger.warning('RPC (with shmem) failed with: %s' % err.details())
                        self._del_shmem()
                        self._use_shmem = False
                        self._logger.info('No longer using shared memory for CentroidsRequest() calls')
                        # Fall through to non-shmem path.
                    else:
                        self._logger.error('RPC (with shmem) failed with: %s' % err.details())
                        rpc_exception = err
                        continue  # Loop to retry logic.

            if not self._use_shmem:
                # Not using shared memory. The image data is passed as part of the
                # gRPC request.
                im = cedar_detect_pb2.Image(width=width, height=height,
                                            image_data=np_image.tobytes())
                req = cedar_detect_pb2.CentroidsRequest(
                    input_image=im, sigma=sigma, return_binned=False,
                    binning=binning, use_binned_for_star_candidates=use_binned,
                    detect_hot_pixels=detect_hot_pixels, normalize_rows=normalize_rows)
                try:
                    centroids_result = self._get_stub().ExtractCentroids(req)
                    break  # Succeeded, break out of retry loop.
                except grpc.RpcError as err:
                    self._logger.error('RPC failed with: %s' % err.details())
                    rpc_exception = err  # Loop to retry logic.
        # while True

        tetra_centroids = []  # List of (y, x).
        if centroids_result is not None:
            for sc in centroids_result.star_candidates:
                tetra_centroids.append((sc.centroid_position.y, sc.centroid_position.x))
        return tetra_centroids
