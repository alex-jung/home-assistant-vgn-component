"""Exceptions for VGN requests."""


class VgnGetError(IOError):
    """Custom exception to be thrown if get request to VGN API does not succeed."""


class GtfsFileNotFound(IOError):
    """Custom exception to be thrown if GTFS.zip file was not found on default location /data/GTFS.zip."""
