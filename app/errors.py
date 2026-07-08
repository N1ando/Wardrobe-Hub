"""Domain exceptions raised by the measurement pipeline."""


class MeasurementError(Exception):
    """Base class for measurement-pipeline failures."""


class ImageDecodeError(MeasurementError):
    """Raised when an uploaded file cannot be decoded as an image."""


class NoPersonDetectedError(MeasurementError):
    """Raised when no usable subject silhouette is found in an image."""
