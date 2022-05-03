from pydantic import BaseModel, Field


class ConnectionErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Connection error."},
        }


class NotFoundErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Resource was not found."},
        }


class BadRequestErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Bad request."},
        }


class ResponseSchema(BaseModel):
    message: str = Field(..., example="Success")


class ColabCredentials(BaseModel):
    user: str = Field(..., example="root")
    password: str = Field(..., example="PASSWORD")
    host: str = Field(..., example="x.tcp.ngrok.io")
    port: int = Field(..., example=12345)


class DownloadColabSchema(ColabCredentials):
    keys_prefix: str = Field(..., example="script_files")


class UploadColabSchema(DownloadColabSchema):
    script_name: str = Field(None, example="script.py")
