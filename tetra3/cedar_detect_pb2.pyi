from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CentroidsRequest(_message.Message):
    __slots__ = ("input_image", "sigma", "max_size", "binning", "return_binned", "use_binned_for_star_candidates", "detect_hot_pixels", "estimate_background_region")
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    SIGMA_FIELD_NUMBER: _ClassVar[int]
    MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    BINNING_FIELD_NUMBER: _ClassVar[int]
    RETURN_BINNED_FIELD_NUMBER: _ClassVar[int]
    USE_BINNED_FOR_STAR_CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    DETECT_HOT_PIXELS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATE_BACKGROUND_REGION_FIELD_NUMBER: _ClassVar[int]
    input_image: Image
    sigma: float
    max_size: int
    binning: int
    return_binned: bool
    use_binned_for_star_candidates: bool
    detect_hot_pixels: bool
    estimate_background_region: Rectangle
    def __init__(self, input_image: _Optional[_Union[Image, _Mapping]] = ..., sigma: _Optional[float] = ..., max_size: _Optional[int] = ..., binning: _Optional[int] = ..., return_binned: bool = ..., use_binned_for_star_candidates: bool = ..., detect_hot_pixels: bool = ..., estimate_background_region: _Optional[_Union[Rectangle, _Mapping]] = ...) -> None: ...

class Rectangle(_message.Message):
    __slots__ = ("origin_x", "origin_y", "width", "height")
    ORIGIN_X_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_Y_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    origin_x: int
    origin_y: int
    width: int
    height: int
    def __init__(self, origin_x: _Optional[int] = ..., origin_y: _Optional[int] = ..., width: _Optional[int] = ..., height: _Optional[int] = ...) -> None: ...

class CentroidsResult(_message.Message):
    __slots__ = ("noise_estimate", "background_estimate", "hot_pixel_count", "peak_star_pixel", "star_candidates", "binned_image", "algorithm_time")
    NOISE_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    BACKGROUND_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    HOT_PIXEL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PEAK_STAR_PIXEL_FIELD_NUMBER: _ClassVar[int]
    STAR_CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    BINNED_IMAGE_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_TIME_FIELD_NUMBER: _ClassVar[int]
    noise_estimate: float
    background_estimate: float
    hot_pixel_count: int
    peak_star_pixel: int
    star_candidates: _containers.RepeatedCompositeFieldContainer[StarCentroid]
    binned_image: Image
    algorithm_time: _duration_pb2.Duration
    def __init__(self, noise_estimate: _Optional[float] = ..., background_estimate: _Optional[float] = ..., hot_pixel_count: _Optional[int] = ..., peak_star_pixel: _Optional[int] = ..., star_candidates: _Optional[_Iterable[_Union[StarCentroid, _Mapping]]] = ..., binned_image: _Optional[_Union[Image, _Mapping]] = ..., algorithm_time: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class Image(_message.Message):
    __slots__ = ("width", "height", "image_data", "shmem_name")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    SHMEM_NAME_FIELD_NUMBER: _ClassVar[int]
    width: int
    height: int
    image_data: bytes
    shmem_name: str
    def __init__(self, width: _Optional[int] = ..., height: _Optional[int] = ..., image_data: _Optional[bytes] = ..., shmem_name: _Optional[str] = ...) -> None: ...

class StarCentroid(_message.Message):
    __slots__ = ("centroid_position", "brightness", "num_saturated")
    CENTROID_POSITION_FIELD_NUMBER: _ClassVar[int]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    NUM_SATURATED_FIELD_NUMBER: _ClassVar[int]
    centroid_position: ImageCoord
    brightness: float
    num_saturated: int
    def __init__(self, centroid_position: _Optional[_Union[ImageCoord, _Mapping]] = ..., brightness: _Optional[float] = ..., num_saturated: _Optional[int] = ...) -> None: ...

class ImageCoord(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...
