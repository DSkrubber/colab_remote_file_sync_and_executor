import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator, Union

from botocore.response import StreamingBody
from paramiko import AutoAddPolicy, SSHClient, SSHException

from .constants import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    COLAB_OUTPUT_DIRECTORY,
    COLAB_UPLOAD_DIRECTORY,
    S3_ENDPOINT_URL,
)
from .errors import FileIntegrityError
from .logger import get_logger
from .schemas import DownloadColabSchema

colab_logger = get_logger(__name__)


@contextmanager
def connect_ssh_colab(credentials: DownloadColabSchema) -> Iterator[SSHClient]:
    """Connects to colab via ssh with provided credentials and returns client.

    :param credentials: credentials generated colab_ssh_config_script on colab.
    :return: iterator that yields paramiko SSHClient.
    """
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh_client.connect(
            hostname=credentials.host,
            port=credentials.port,
            username=credentials.user,
            password=credentials.password,
        )
        yield ssh_client
    except SSHException as error:
        colab_logger.warning(f"Colab SSH connection error: {error}")
        raise
    finally:
        ssh_client.close()


def upload_file_to_colab(
    ssh_client: SSHClient,
    file_obj: Union[StreamingBody, BinaryIO],
    file_size: int,
    file_name: str,
) -> None:
    """Upload files into colab /content/uploaded directory.

    If file was corrupted during upload - raises FileIntegrityError exception.
    :param ssh_client: paramiko ssh client connected to colab session.
    :param file_obj: file-like object to upload.
    :param file_size: size of file object in bytes.
    :param file_name: name of uploaded file object.
    :return: None.
    """
    ssh_client.exec_command(f"mkdir -p {COLAB_UPLOAD_DIRECTORY}")
    file_path = f"{COLAB_UPLOAD_DIRECTORY}/{file_name}"
    with ssh_client.open_sftp() as sftp_session:
        response = sftp_session.putfo(file_obj, file_path, confirm=True)
    if response.st_size != file_size:
        colab_logger.warning(f"File {file_name} was corrupted during upload")
        raise FileIntegrityError(
            f"File {file_name} was corrupted during upload"
        )


def execute_script(ssh_client: SSHClient, script_name: str) -> None:
    """Executes uploaded script with provided script_name on colab.

    If script has .ipynb extension - firstly converts script to .py extension.
    :param ssh_client: paramiko ssh client connected to colab session.
    :param script_name: name of script to execute
    :return: None.
    """
    run_command = "python {0}"
    script_name_path = Path(f"{COLAB_UPLOAD_DIRECTORY}/{script_name}")
    if script_name_path.suffix == ".ipynb":
        colab_logger.info(
            f"Convert script {script_name_path} from ipynb to py"
        )
        try:
            run_command = (
                f"jupyter nbconvert {script_name_path} --to python; "
                f"rm {script_name_path}; {run_command}"
            )
            script_name_path = script_name_path.with_suffix(".py")
        except SSHException as error:
            colab_logger.warning(f"Script conversion error: {error}")
    try:
        ssh_client.exec_command(run_command.format(script_name_path))
    except SSHException as error:
        colab_logger.warning(f"Script execution error: {error}")


def get_aws_credentials(home_directory: Path) -> None:
    """Checks that required for aws CLI connections credentials file exists.

    File should be located at ~/.aws/ directory. If not exists - creates that
    directory and file with minio connection credentials.
    :param home_directory: absolute path to user's home directory.
    :return: None.
    """
    credentials_file = home_directory / ".aws" / "credentials"
    if not credentials_file.is_file():
        colab_logger.info("Creating credentials file...")
        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        with credentials_file.open("w") as cred_file:
            cred_file.writelines(
                (
                    "[default]\n",
                    f"aws_access_key_id={AWS_ACCESS_KEY_ID}\n",
                    f"aws_secret_access_key={AWS_SECRET_ACCESS_KEY}\n",
                ),
            )
    colab_logger.info("AWS credentials file provided")


def local_mount_colab_directory(
    local_directory: str, colab_info: DownloadColabSchema
) -> None:
    """Mount remote colab directory using sshfs connection to local directory.

    :param local_directory: mounting directory path in application container.
    :param colab_info: credentials for sshfs connection.
    :return: None.
    """
    mount_command = (
        f"sshfs -o StrictHostKeyChecking=no,password_stdin "
        f"-p {colab_info.port} {colab_info.user}@{colab_info.host}:"
        f"{COLAB_OUTPUT_DIRECTORY} {local_directory}"
    )
    try:
        subprocess.run(
            mount_command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            input=colab_info.password,
        )
    except subprocess.SubprocessError as error:
        colab_logger.warning(f"sshfs connection error: {error}")
        raise


def sync_files_with_minio(
    local_directory: str, bucket: str, colab_info: DownloadColabSchema
) -> None:
    """Synchronize files on colab and files in minio storage.

    Minio files will be located at <colab_info.keys_prefix>/output/ directory.
    After files transfer - unmounts remote directory.
    :param local_directory: mounting directory path in application container.
    :param bucket: bucket to upload file into.
    :param colab_info: credentials for minio and colab connection.
    :return: None.
    """
    keys_prefix = colab_info.keys_prefix.strip("/") + "/"
    sync_command = (
        f"aws --endpoint-url {S3_ENDPOINT_URL} s3 sync {local_directory} "
        f"s3://{bucket}/{keys_prefix}/output/ --delete"
    )
    try:
        subprocess.run(
            sync_command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.SubprocessError as error:
        colab_logger.warning(f"Files synchronization error: {error}")
        raise
    finally:
        subprocess.run(f"fusermount -u {local_directory}", shell=True)
        colab_logger.info("Remote directory successfully unmounted")
