import subprocess

import grpc
from multiprocessing import shared_memory
import numpy as np
from PIL import Image

import cedar_detect_pb2
import cedar_detect_pb2_grpc

# Use shared memory to make the gRPC calls faster. This works only when the
# client (this program) and the CedarDetect gRPC server are running on the same
# machine.
USE_SHMEM = True

class CedarDetectClient():
    """TODO: summarize
    """

    def __init__(self, binary_path='bin/cedar-detect-server', port=50051):
        """TODO: describe
        """
        self._binary_path = binary_path
        self._port = port
        self._subprocess = subprocess.Popen([self._binary_path, '--port', str(self._port)])
        # Will initialize on first use.
        self._stub = None
        self._shmem = None
        self._shmem_size = 0

    def __del__(self):
        self._subprocess.kill()
        if self._shmem is not None:
            self._shmem.close()
            self._shmem.unlink()

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

    def _extract_centroids_rpc(self, image, sigma, max_size, use_binned):
        cr = cedar_detect_pb2.CentroidsRequest(
            input_image=image, sigma=sigma, max_size=max_size, return_binned=False,
            use_binned_for_star_candidates=use_binned)
        return self._get_stub().ExtractCentroids(cr)

    def extract_centroids(self, image, sigma, max_size, use_binned):
        """TODO: describe
        """
        np_image = np.asarray(image, dtype=np.uint8)
        (height, width) = np_image.shape

        centroids_result = None
        im = None
        if USE_SHMEM:
            # Using shared memory. The image data is passed in a shared memory
            # object, with the gRPC request giving the name of the shared memory
            # object.
            self._alloc_shmem(size=width*height)
            # Create numpy array backed by shmem.
            shimg = np.ndarray(np_image.shape, dtype=np_image.dtype, buffer=self._shmem.buf)
            # Copy np_image into shimg. This is much cheaper than passing image
            # over the gRPC call.
            shimg[:] = np_image[:]

            im = cedar_detect_pb2.Image(width=width, height=height,
                                        shmem_name=self._shmem.name)
        else:
            # Not using shared memory. The image data is passed as part of the
            # gRPC request.
            im = cedar_detect_pb2.Image(width=width, height=height,
                                        image_data=np_image.tobytes())

        centroids_result = self._extract_centroids_rpc(im, sigma, max_size, use_binned)

        tetra_centroids = []  # List of (y, x).
        for sc in centroids_result.star_candidates:
            tetra_centroids.append((sc.centroid_position.y, sc.centroid_position.x))
        return tetra_centroids
