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

    def __init__(self, binary_path: Union[Path, str, None] = None, port=50051):
        """Spawns the cedar-detect-server subprocess.

        Args:
            binary_path: If you wish to specify a custom location for the `cedar-detect-server` binary you
                may do so, otherwise the default is to search in the relative directory "./bin"
            port: Customize the `cedar-detect-server` port if running multiple instances.
        """
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

    def _alloc_shmem(self, size):
        if self._shmem is not None and size > self._shmem_size:
            self._shmem.close()
            self._shmem.unlink()
            self._shmem = None
        if self._shmem is None:
            self._shmem = shared_memory.SharedMemory(
                "/cedar_detect_image", create=True, size=size)
            self._shmem_size = size

    def _del_shmem(self):
        if self._shmem is not None:
            self._shmem.close()
            self._shmem.unlink()
            self._shmem = None

    def extract_centroids(self, image, sigma, max_size, use_binned, binning=None,
                          detect_hot_pixels=True):
        """Invokes the CedarDetect.ExtractCentroids() RPC. Returns [(y,x)] of the
        detected star centroids.
        """
        np_image = np.asarray(image, dtype=np.uint8)
        (height, width) = np_image.shape

        centroids_result = None
        im = None
        if self._use_shmem:
            # Use shared memory to make the gRPC calls faster. This works only
            # when the client (this program) and the CedarDetect gRPC server are
            # running on the same machine.

            # The image data is passed in a shared memory object, with the gRPC
            # request giving the name of the shared memory object.
            self._alloc_shmem(size=width*height)
            # Create numpy array backed by shmem.
            shimg = np.ndarray(np_image.shape, dtype=np_image.dtype, buffer=self._shmem.buf)
            # Copy np_image into shimg. This is much cheaper than passing image
            # over the gRPC call.
            shimg[:] = np_image[:]

            im = cedar_detect_pb2.Image(width=width, height=height,
                                        shmem_name=self._shmem.name)
            req = cedar_detect_pb2.CentroidsRequest(
                input_image=im, sigma=sigma, max_size=max_size, return_binned=False,
                binning=binning, use_binned_for_star_candidates=use_binned,
                detect_hot_pixels=detect_hot_pixels)
            try:
                centroids_result = self._get_stub().ExtractCentroids(req,
                                                                     wait_for_ready=True)
            except grpc.RpcError as err:
                if err.code() == grpc.StatusCode.INTERNAL:
                    logging.warning('RPC failed with: %s' % err.details())
                    self._del_shmem()
                    self._use_shmem = False
                    logging.info('No longer using shared memory for CentroidsRequest() calls')
                else:
                    logging.error('RPC (with shmem) failed with: %s' % err.details())

        if not self._use_shmem:
            # Not using shared memory. The image data is passed as part of the
            # gRPC request.
            im = cedar_detect_pb2.Image(width=width, height=height,
                                        image_data=np_image.tobytes())
            req = cedar_detect_pb2.CentroidsRequest(
                input_image=im, sigma=sigma, max_size=max_size, return_binned=False,
                use_binned_for_star_candidates=use_binned)
            try:
                centroids_result = self._get_stub().ExtractCentroids(req)
            except grpc.RpcError as err:
                logging.error('RPC failed with: %s' % err.details())

        tetra_centroids = []  # List of (y, x).
        if centroids_result is not None:
            for sc in centroids_result.star_candidates:
                tetra_centroids.append((sc.centroid_position.y, sc.centroid_position.x))
        return tetra_centroids
