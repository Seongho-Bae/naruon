import zipfile
from pathlib import Path
from typing import List, Union

from .exceptions import InvalidArchiveError, ArchiveSizeExceededError, ArchiveFileCountExceededError

MAX_EXTRACT_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB
MAX_FILE_COUNT = 100000

def extract_backup(zip_path: Union[str, Path], output_dir: Union[str, Path]) -> List[str]:
    """
    Extracts a zip archive to the specified output directory.
    
    WARNING: This function performs blocking I/O operations. When called from
    an async web layer (e.g. FastAPI), it must be executed in a thread pool using
    `fastapi.concurrency.run_in_threadpool` or `asyncio.to_thread()`.
    
    Args:
        zip_path: The path to the zip archive to extract.
        output_dir: The directory where the contents should be extracted.
        
    Returns:
        A list of string paths to the extracted files (excluding directories).
        
    Raises:
        InvalidArchiveError: If the zip file is not found or corrupted.
        ArchiveSizeExceededError: If the uncompressed size exceeds the maximum allowed limit.
    """
    zip_path = Path(zip_path)
    output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            total_size = 0
            file_count = 0
            
            # Check for zip bomb and file count limit
            for info in z.infolist():
                total_size += info.file_size
                if total_size > MAX_EXTRACT_SIZE:
                    raise ArchiveSizeExceededError(f"Archive exceeds maximum allowed extraction size of {MAX_EXTRACT_SIZE} bytes.")
                
                file_count += 1
                if file_count > MAX_FILE_COUNT:
                    raise ArchiveFileCountExceededError(f"Archive exceeds maximum allowed file count of {MAX_FILE_COUNT}.")
            
            # Extract files securely
            for info in z.infolist():
                if not info.is_dir():
                    extracted_path = z.extract(info, output_dir)
                    extracted_paths.append(str(extracted_path))
                    
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        raise InvalidArchiveError(f"Failed to extract archive: {e}") from e
        
    return extracted_paths
