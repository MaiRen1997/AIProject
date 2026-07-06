import asyncio
import base64
import mimetypes
import urllib.request
from datetime import datetime

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_ai.dao.ai_model_dao import AiModelDao
from module_ai.entity.vo.ai_model_vo import AiModelModel
from module_ai.entity.vo.text_to_image_vo import TextToImageRequestModel, TextToImageResultModel
from utils.common_util import CamelCaseUtil
from utils.crypto_util import CryptoUtil


class TextToImageService:
    """文生图服务层。"""

    @classmethod
    async def generate_image_services(
        cls, query_db: AsyncSession, request: TextToImageRequestModel
    ) -> TextToImageResultModel:
        model_config = await cls._load_model_config(query_db, request.model_id)
        return await asyncio.to_thread(cls._generate_image_sync, model_config, request)

    @classmethod
    async def _load_model_config(cls, query_db: AsyncSession, model_id: int | None) -> AiModelModel:
        if model_id:
            ai_model = await AiModelDao.get_ai_model_detail_by_id(query_db, model_id)
            if not ai_model:
                raise ServiceException(message='指定的图片模型不存在')
        else:
            ai_model = await AiModelDao.get_first_available_image_model(query_db)
            if not ai_model:
                raise ServiceException(message='未找到可用的图片模型，请先在模型管理中配置 supportImages=Y 且状态正常的模型')

        model_config = AiModelModel(**CamelCaseUtil.transform_result(ai_model))
        if model_config.status != '0':
            raise ServiceException(message='当前图片模型已停用')
        if model_config.support_images != 'Y':
            raise ServiceException(message='当前模型未开启图片生成功能')
        if not model_config.model_code:
            raise ServiceException(message='当前模型缺少 model_code 配置')
        if not model_config.api_key:
            raise ServiceException(message='当前模型缺少 API Key 配置')

        return model_config

    @classmethod
    def _build_client(cls, model_config: AiModelModel) -> OpenAI:
        real_api_key = CryptoUtil.decrypt(model_config.api_key)
        if not real_api_key:
            raise ServiceException(message='当前模型 API Key 解密失败或为空')
        return OpenAI(api_key=real_api_key, base_url=model_config.base_url or None)

    @classmethod
    def _generate_image_sync(
        cls, model_config: AiModelModel, request: TextToImageRequestModel
    ) -> TextToImageResultModel:
        client = cls._build_client(model_config)

        generate_kwargs = {
            'model': model_config.model_code,
            'prompt': request.prompt,
            'size': request.size or '1024x1024',
            'quality': request.quality or 'standard',
            'n': 1,
        }

        try:
            response = client.images.generate(**generate_kwargs)
        except Exception as e:
            raise ServiceException(message=f'图片生成失败: {e}') from e

        data_list = getattr(response, 'data', None) or []
        if not data_list:
            raise ServiceException(message='图片生成失败: 模型未返回图片数据')

        item = data_list[0]
        image_url = getattr(item, 'url', None)
        revised_prompt = getattr(item, 'revised_prompt', None)
        mime_type = 'image/png'
        image_data_url = None

        b64_json = getattr(item, 'b64_json', None) or getattr(item, 'b64', None)
        if b64_json:
            image_data_url = f'data:{mime_type};base64,{b64_json}'
        elif image_url:
            image_data_url, mime_type = cls._download_image_as_data_url(image_url)

        if not image_data_url and not image_url:
            raise ServiceException(message='图片生成失败: 未获取到可展示的图片内容')

        extension = mimetypes.guess_extension(mime_type) or '.png'
        download_filename = f'text-to-image-{datetime.now().strftime("%Y%m%d%H%M%S")}{extension}'

        return TextToImageResultModel(
            prompt=request.prompt,
            revisedPrompt=revised_prompt,
            imageDataUrl=image_data_url,
            imageUrl=image_url,
            downloadFilename=download_filename,
            modelId=model_config.model_id,
            modelCode=model_config.model_code,
            provider=model_config.provider or 'OpenAI',
        )

    @classmethod
    def _download_image_as_data_url(cls, image_url: str) -> tuple[str, str]:
        try:
            with urllib.request.urlopen(image_url, timeout=30) as resp:
                image_bytes = resp.read()
                mime_type = resp.headers.get_content_type() or 'image/png'
        except Exception as e:
            raise ServiceException(message=f'图片已生成，但下载模型返回的图片链接失败: {e}') from e

        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f'data:{mime_type};base64,{encoded}', mime_type
