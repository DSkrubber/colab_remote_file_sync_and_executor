import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

APP_HOST = os.environ.get("APP_HOST")
APP_PORT = os.environ.get("APP_PORT")
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

ROUTES_PREFIX = "/files"
COLAB_UPLOAD_DIRECTORY = "/content/uploaded"
COLAB_OUTPUT_DIRECTORY = f"{COLAB_UPLOAD_DIRECTORY}/output"
TAG = "Colab and Minio resources"
