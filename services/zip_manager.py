"""
ZIP Manager Service — creates a ZIP archive of the entire output folder.
"""

import io
import os
import zipfile


def create_zip(folder_path: str) -> bytes:
    """
    Create a ZIP archive of the given folder and return it as bytes.
    Preserves the internal folder structure.
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            # Skip hidden files/directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                if file.startswith("."):
                    continue
                file_path = os.path.join(root, file)
                # Use relative path inside zip to avoid full system paths
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                zf.write(file_path, arcname)

    buffer.seek(0)
    return buffer.read()