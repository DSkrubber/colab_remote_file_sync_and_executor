from subprocess import SubprocessError

from botocore.exceptions import BotoCoreError, ClientError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from paramiko import SSHException


class NoSuchBucket(Exception):
    """Custom exception that will be raised if minio bucket doesn't exist."""

    def __init__(self, message: str):
        self.message = message


class FileIntegrityError(Exception):
    """Custom exception that will be raised if uploaded file was corrupted."""

    def __init__(self, message: str):
        self.message = message


def botocore_error_handler(
    request: Request, exc: BotoCoreError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc}"},
    )


def no_such_bucket_error_handler(
    request: Request, exc: NoSuchBucket
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc.message}"},
    )


def minio_client_error_handler(
    request: Request, exc: ClientError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc}"},
    )


def ssh_connection_error_handler(
    request: Request, exc: SSHException
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc}"},
    )


def subprocess_run_error_handler(
    request: Request, exc: SubprocessError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc}"},
    )


def file_integrity_error_handler(
    request: Request, exc: FileIntegrityError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: {exc.message}"},
    )
