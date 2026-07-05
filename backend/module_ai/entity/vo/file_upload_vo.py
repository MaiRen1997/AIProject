from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AiUploadResponseModel(BaseModel):
    """
    AI文件上传响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    file_name: str = Field(description='文件名')
    new_file_name: str = Field(description='新文件名称')
    original_filename: str = Field(description='原文件名称')
    storage_path: str = Field(description='文件存储绝对路径')
