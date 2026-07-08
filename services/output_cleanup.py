"""
Output folder cleanup — 30-minute expiry and best-effort session-end deletion.
"""

import os
import shutil
import time

from streamlit.runtime.scriptrunner import get_script_run_ctx

OUTPUT_RETENTION_MINUTES = int(os.getenv("OUTPUT_RETENTION_MINUTES", "1440"))  # 24h default

_STARTUP_CLEANUP_DONE = False
_SESSION_OUTPUT_FOLDERS: dict[str, str] = {}


def get_outputs_base_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def delete_output_folder_silent(folder_path: str) -> None:
    """Delete an output folder without raising errors to the user."""
    if not folder_path or not os.path.isdir(folder_path):
        return
    try:
        shutil.rmtree(folder_path, ignore_errors=True)
    except OSError:
        pass


def cleanup_old_output_folders(max_age_minutes: int = OUTPUT_RETENTION_MINUTES) -> None:
    """Delete output folders older than max_age_minutes based on folder mtime."""
    from services.video_store import output_folder_has_videos

    base = get_outputs_base_dir()
    if not os.path.isdir(base):
        return

    cutoff = time.time() - (max_age_minutes * 60)
    for name in os.listdir(base):
        path = os.path.join(base, name)
        if not os.path.isdir(path):
            continue
        try:
            if output_folder_has_videos(path):
                continue
            if os.path.getmtime(path) < cutoff:
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass


def run_startup_cleanup_once() -> None:
    """Run age-based cleanup once per Streamlit server process."""
    global _STARTUP_CLEANUP_DONE
    if _STARTUP_CLEANUP_DONE:
        return
    cleanup_old_output_folders()
    _STARTUP_CLEANUP_DONE = True


def get_streamlit_session_id() -> str | None:
    ctx = get_script_run_ctx()
    if ctx is None:
        return None
    return ctx.session_id


def register_session_output_folder(session_id: str | None, folder_path: str) -> None:
    """Track which output folder belongs to the active browser session."""
    if not session_id or not folder_path:
        return
    _SESSION_OUTPUT_FOLDERS[session_id] = folder_path


def try_cleanup_session_output_folder(session_id: str | None) -> None:
    """
    Best-effort cleanup when session state no longer holds results.
    Skips folders that contain saved video files.
    """
    from services.video_store import output_folder_has_videos

    if not session_id:
        return
    folder = _SESSION_OUTPUT_FOLDERS.pop(session_id, None)
    if folder and not output_folder_has_videos(folder):
        delete_output_folder_silent(folder)
