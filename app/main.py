import logging
from pathlib import Path
from subprocess import SubprocessError
from tempfile import TemporaryDirectory
from typing import List

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, Form, Header, UploadFile, status
from fastapi.responses import Response
from paramiko import SSHException

from .colab_functions import (
    connect_ssh_colab,
    execute_script,
    get_aws_credentials,
    local_mount_colab_directory,
    sync_files_with_minio,
    upload_file_to_colab,
)
from .constants import ROUTES_PREFIX
from .errors import (
    FileIntegrityError,
    NoSuchBucket,
    botocore_error_handler,
    file_integrity_error_handler,
    minio_client_error_handler,
    no_such_bucket_error_handler,
    ssh_connection_error_handler,
    subprocess_run_error_handler,
)
from .logger import get_logger
from .minio_functions import (
    clear_minio_prefix,
    get_minio_client,
    get_minio_object,
    list_minio_prefix_files,
    upload_file_to_minio,
)
from .schemas import (
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    DownloadColabSchema,
    NotFoundErrorSchema,
    ResponseSchema,
    UploadColabSchema,
)

app = FastAPI(
    title="Colab SSH uploader and executor",
    version="0.1.0",
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
)
app.add_exception_handler(BotoCoreError, botocore_error_handler)
app.add_exception_handler(NoSuchBucket, no_such_bucket_error_handler)
app.add_exception_handler(ClientError, minio_client_error_handler)
app.add_exception_handler(SSHException, ssh_connection_error_handler)
app.add_exception_handler(SubprocessError, subprocess_run_error_handler)
app.add_exception_handler(FileIntegrityError, file_integrity_error_handler)

main_logger = get_logger(__name__)


@app.put(
    f"{ROUTES_PREFIX}/upload_minio",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Upload multiple files to minio storage using multipart/form-data",
)
def upload_minio_files(
    files: List[UploadFile],
    keys_prefix: str = Form(..., example="project_1/script_files"),
    bucket: str = Header(..., example="root"),
) -> Response:
    """Custom key_prefix will be added to uploaded files names. In order to
    make resource idempotent - will remove all files that have the same prefix
    from storage before upload.
    """
    logging.info("STARTING")
    keys_prefix = keys_prefix.strip("/")
    minio_client = get_minio_client(bucket)
    clear_minio_prefix(minio_client, bucket, keys_prefix)
    for file_object in files:
        file_key = f"{keys_prefix}/{file_object.filename}"
        upload_file_to_minio(minio_client, file_object.file, file_key, bucket)
    main_logger.info(f"Files were uploaded to colab with {keys_prefix}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    f"{ROUTES_PREFIX}/upload_colab",
    status_code=status.HTTP_200_OK,
    response_model=ResponseSchema,
    summary="Upload files with specified prefix from minio storage to colab.",
)
def upload_files_to_colab(
    upload_info: UploadColabSchema,
    bucket: str = Header(..., example="root"),
) -> ResponseSchema:
    """All uploaded files will be stored at "/content/uploaded/" directory.
    If script_name with python script provided - executes script. In order to
    use download resource make sure to save script results at
    "/content/uploaded/output/" directory.
    """
    minio_client = get_minio_client(bucket)
    keys_prefix = upload_info.keys_prefix.strip("/") + "/"
    files = list_minio_prefix_files(minio_client, bucket, keys_prefix)
    response_message = f"Successfully upload files from {keys_prefix} on colab"
    with connect_ssh_colab(upload_info) as ssh_client:
        for file_obj in files:
            file_key = file_obj["Key"]
            file_name = Path(file_key).name
            file_object, file_size = get_minio_object(
                minio_client, bucket, file_key
            )
            upload_file_to_colab(ssh_client, file_object, file_size, file_name)
        main_logger.info(f"Files from {keys_prefix} were uploaded to colab")
        if upload_info.script_name:
            script_name = upload_info.script_name
            execute_script(ssh_client, script_name)
            main_logger.info("Successfully start execution of script")
            response_message = (
                f"{response_message} and start executing of {script_name}"
            )
    return ResponseSchema.parse_obj({"message": response_message})


@app.post(
    f"{ROUTES_PREFIX}/download_colab",
    status_code=status.HTTP_200_OK,
    response_model=ResponseSchema,
    summary="Load script results from colab to minio storage",
)
def sync_files_from_colab(
    download_info: DownloadColabSchema,
    bucket: str = Header(..., example="root"),
) -> ResponseSchema:
    """Output files should be stored at "/content/uploaded/output/" directory.
    This resource may be used to sync files on colab and files in minio storage
    with provided keys_prefix. This means that if new file was created on colab
    directory - it will be uploaded to minio, if file was deleted in colab - it
    will be removed in minio. If file didn't change - it won't be modified in
    minio.
    """
    home_directory = Path.home()
    get_aws_credentials(home_directory)
    with TemporaryDirectory(dir=home_directory) as temp_directory:
        local_mount_colab_directory(temp_directory, download_info)
        sync_files_with_minio(temp_directory, bucket, download_info)
    response_message = f"Successfully download colab files to bucket {bucket}"
    main_logger.info(response_message)
    return ResponseSchema.parse_obj({"message": response_message})
