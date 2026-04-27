import asyncio
import zipfile
from pathlib import Path

from .exceptions import InvalidArchiveError, ArchiveSizeExceededError, ArchiveFileCountExceededError

MAX_EXTRACT_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB
MAX_FILE_COUNT = 100000

def extract_backup(zip_path: str | Path, output_dir: str | Path) -> list[Path]:
    """
    Extracts a zip archive to the specified output directory.
    
    WARNING: This function performs blocking I/O operations. When called from
    an async web layer (e.g. FastAPI), it must be executed in a thread pool using
    `fastapi.concurrency.run_in_threadpool` or `asyncio.to_thread()`.
    
    Args:
        zip_path: The path to the zip archive to extract.
        output_dir: The directory where the contents should be extracted.
        
    Returns:
        A list of Path objects for the extracted files (excluding directories).
        
    Raises:
        InvalidArchiveError: If the zip file is not found or corrupted.
        ArchiveSizeExceededError: If the uncompressed size exceeds the maximum allowed limit.
        ArchiveFileCountExceededError: If the archive exceeds the maximum allowed file count.
    """
    zip_path = Path(zip_path)
    output_dir = Path(output_dir).resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            total_size = 0
            file_count = 0
            
            for info in z.infolist():
                if info.is_dir():
                    continue

                file_count += 1
                if file_count > MAX_FILE_COUNT:
                    raise ArchiveFileCountExceededError(f"Archive exceeds maximum allowed file count of {MAX_FILE_COUNT}.")
                
                # Sanitize path to prevent traversal
                parts = [p for p in info.filename.replace('\\', '/').split('/') if p not in ('', '.', '..')]
                if not parts:
                    continue
                safe_name = "/".join(parts)
                
                target_path = (output_dir / safe_name).resolve()
                
                # Double-check that it is within output_dir
                if not str(target_path).startswith(str(output_dir)):
                    continue
                
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                with z.open(info) as source, open(target_path, "wb") as target:
                    while chunk := source.read(8192):
                        total_size += len(chunk)
                        if total_size > MAX_EXTRACT_SIZE:
                            raise ArchiveSizeExceededError(f"Archive exceeds maximum allowed extraction size of {MAX_EXTRACT_SIZE} bytes.")
                        target.write(chunk)
                
                extracted_paths.append(target_path)
                    
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        raise InvalidArchiveError(f"Failed to extract archive: {e}") from e
        
    return extracted_paths

async def extract_backup_async(zip_path: str | Path, output_dir: str | Path) -> list[Path]:
    """
    Async wrapper for extract_backup to be used safely in async contexts.
    """
    return await asyncio.to_thread(extract_backup, zip_path, output_dir)

