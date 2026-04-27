import zipfile
import os
from typing import List

def extract_backup(zip_path: str, output_dir: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    extracted_paths = []
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(output_dir)
        for name in z.namelist():
            extracted_paths.append(os.path.join(output_dir, name))
    return extracted_paths
