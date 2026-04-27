class ArchiveError(Exception):
    """Base exception for archive operations."""
    pass

class InvalidArchiveError(ArchiveError):
    """Raised when an archive is invalid, corrupted, or not found."""
    pass

class ArchiveSizeExceededError(ArchiveError):
    """Raised when an archive exceeds the maximum allowed extracted size."""
    pass

class ArchiveFileCountExceededError(ArchiveError):
    """Raised when an archive exceeds the maximum allowed number of files."""
    pass
