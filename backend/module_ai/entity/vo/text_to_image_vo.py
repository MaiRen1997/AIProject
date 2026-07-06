from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size


class TextToImageRequestModel(BaseModel):
    """文生图请求模型。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    prompt: str = Field(description='图片描述词')
    model_id: int | None = Field(default=None, description='用于生成图片的模型ID，不传则自动选择可用模型')
    size: Literal['1024x1024', '1536x1024', '1024x1536', 'auto'] | None = Field(
        default='1024x1024', description='生成图片尺寸'
    )
    quality: Literal['standard', 'hd', 'high', 'medium', 'low', 'auto'] | None = Field(
        default='standard', description='图片质量'
    )

    @NotBlank(field_name='prompt', message='提示词不能为空')
    @Size(field_name='prompt', min_length=1, max_length=4000, message='提示词长度不能超过4000个字符')
    def get_prompt(self) -> str:
        return self.prompt


class TextToImageResultModel(BaseModel):
    """文生图响应模型。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    prompt: str = Field(description='原始提示词')
    revised_prompt: str | None = Field(default=None, description='模型修订后的提示词')
    image_data_url: str | None = Field(default=None, description='用于直接展示的 data url')
    image_url: str | None = Field(default=None, description='模型直接返回的图片链接')
    download_filename: str = Field(description='建议下载文件名')
    model_id: int = Field(description='模型ID')
    model_code: str = Field(description='模型编码')
    provider: str = Field(description='模型提供商')
