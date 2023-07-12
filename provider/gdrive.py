from typing import Optional
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

__doc__ = """Wrapper around Google Drive library to simplify usage.
In order to prepare module for work you must:
1. Run get_auth_url() and follow the url in your browser to get verification code.
2. Run auth('your_code') to authenticate.

Then you can use upload(filepath) and download(file_id, destination_path) functions.
"""

g_auth: GoogleAuth = GoogleAuth()
drive: Optional[GoogleDrive] = None


def auth(code: str) -> None:
    global drive
    g_auth.Auth(code)
    drive = GoogleDrive(g_auth)


def get_auth_url() -> str:
    return g_auth.GetAuthUrl()


def upload(source_path: str):
    if drive is None:
        raise Exception("GoogleDrive not initiated. Run 'auth(code)' first.")

    file = drive.CreateFile()
    file.SetContentFile(source_path)
    file.Upload()


def download(file_id: str, destination_path: str):
    if drive is None:
        raise Exception("GoogleDrive not initiated. Run 'auth(code)' first.")

    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(destination_path)
