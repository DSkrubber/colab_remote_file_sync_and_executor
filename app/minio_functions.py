from typing import IO, Any, Dict, List, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from botocore.response import StreamingBody

from .constants import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_ENDPOINT_URL,
)
from .errors import NoSuchBucket
from .logger import get_logger

minio_logger = get_logger(__name__)


def get_minio_client(bucket_name: str) -> boto3.client:
    """Connects to minio storage, checks that bucket exists and returns client.

    :param bucket_name: bucket to check existence.
    :return: boto3 client.
    """
    minio_client = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        minio_client.head_bucket(Bucket=bucket_name)
    except ClientError as error:
        minio_logger.warning(f"Minio connection error: {error}")
        if "404" in error.args[0]:
            raise NoSuchBucket(f"Bucket {bucket_name} doesn't exist")
        raise
    return minio_client


def upload_file_to_minio(
    minio_client: boto3.client,
    file_obj: IO[Any],
    object_key: str,
    bucket: str,
) -> None:
    """Uploads file-like object to minio's bucket with specified key.

    :param minio_client: boto3 client connected to minio storage.
    :param file_obj: file-like object to upload.
    :param object_key: storage key of file to upload.
    :param bucket: bucket to upload file into.
    :return: None.
    """
    try:
        minio_client.upload_fileobj(
            Fileobj=file_obj, Bucket=bucket, Key=object_key
        )
    except (ClientError, BotoCoreError) as error:
        minio_logger.warning(f"Minio file upload error: {error}")
        raise
    minio_logger.info(f"Successfully uploaded files to bucket {bucket}")


def clear_minio_prefix(
    minio_client: boto3.client, bucket: str, prefix: str
) -> None:
    """Clears all objects in storage with specified prefix in keys.

    :param minio_client: boto3 client connected to minio storage.
    :param bucket: bucket to delete files from.
    :param prefix: objects key prefix.
    :return: None.
    """
    files = list_minio_prefix_files(minio_client, bucket, prefix)
    for file_obj in files:
        try:
            minio_client.delete_object(Bucket=bucket, Key=file_obj["Key"])
        except (ClientError, BotoCoreError) as error:
            minio_logger.warning(f"Minio file delete error: {error}")
            raise


FileInfo = List[Dict[str, Any]]


def list_minio_prefix_files(
    minio_client: boto3.client, bucket: str, prefix: str
) -> FileInfo:
    """Returns "Contents" field from result of boto3 list_objects_v2 if exists.

    :param minio_client: boto3 client connected to minio storage.
    :param bucket: bucket to delete files from.
    :param prefix: objects key prefix.
    :return: list of dicts with files properties if exists.
    """
    try:
        files: Dict[str, FileInfo] = minio_client.list_objects_v2(
            Bucket=bucket, Prefix=prefix
        )
        return files.get("Contents", [])
    except (ClientError, BotoCoreError) as error:
        minio_logger.warning(f"Minio list objects error: {error}")
        raise


def get_minio_object(
    minio_client: boto3.client, bucket: str, file_key: str
) -> Tuple[StreamingBody, int]:
    """Gets StreamingBody of file with file_key from minio to upload on colab.

    Returns file-like object from minio storage with size in bytes.
    :param minio_client: boto3 client connected to minio storage.
    :param bucket: bucket to stream files from.
    :param file_key: key of file to stream.
    :return: tuple of file-like StreamingBody object and file size in bytes.
    """
    try:
        file_data = minio_client.get_object(Bucket=bucket, Key=file_key)
        return file_data["Body"], file_data["ContentLength"]
    except (ClientError, BotoCoreError) as error:
        minio_logger.warning(f"Minio list objects error: {error}")
        raise
