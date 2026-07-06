import asyncio
import base64
import json
import mimetypes
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import urllib.request
from datetime import datetime

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
    def _resolve_api_key(cls, model_config: AiModelModel) -> str:
        real_api_key = CryptoUtil.decrypt(model_config.api_key)
        if not real_api_key:
            raise ServiceException(message='当前模型 API Key 解密失败或为空')
        return real_api_key

    @classmethod
    def _resolve_generation_url(cls, model_config: AiModelModel) -> str:
        base_url = (model_config.base_url or 'https://api.siliconflow.cn/v1').strip().rstrip('/')
        parsed = urlparse(base_url)
        path = parsed.path.rstrip('/')
        if path.endswith('/images/generations'):
            return base_url
        if path.endswith('/v1'):
            return f'{base_url}/images/generations'
        if '/v1/' in f'{path}/':
            return f'{base_url}/images/generations'
        return f'{base_url}/v1/images/generations'

    @classmethod
    def _build_payload(cls, model_config: AiModelModel, request: TextToImageRequestModel) -> dict:
        return {
            'model': model_config.model_code,
            'prompt': request.prompt,
            'image_size': request.image_size or '1024x1024',
            'batch_size': max(1, int(request.batch_size or 1)),
            'num_inference_steps': max(1, int(request.num_inference_steps or 20)),
            'guidance_scale': float(request.guidance_scale or 7.5),
        }

    @classmethod
    def _generate_image_sync(
        cls, model_config: AiModelModel, request: TextToImageRequestModel
    ) -> TextToImageResultModel:
        payload = cls._build_payload(model_config, request)
        response = cls._request_siliconflow_generation(model_config, payload)
        image_url, image_data_url, revised_prompt, mime_type = cls._extract_image_payload(response)

        if not image_data_url and not image_url:
            raise ServiceException(message='图片生成失败: 未获取到可展示的图片内容')

        extension = mimetypes.guess_extension(mime_type) or '.png'
        download_filename = f'text-to-image-{datetime.now().strftime("%Y%m%d%H%M%S")}{extension}'

        return TextToImageResultModel(
            prompt=request.prompt,
            revisedPrompt=revised_prompt,
            imageDataUrl=image_data_url,
            imageUrl=image_url,
            requestId=response.get('requestId') or response.get('request_id'),
            downloadFilename=download_filename,
            modelId=model_config.model_id,
            modelCode=model_config.model_code,
            provider=model_config.provider or 'SiliconFlow',
        )

    @classmethod
    def _request_siliconflow_generation(cls, model_config: AiModelModel, payload: dict) -> dict:
        api_key = cls._resolve_api_key(model_config)
        target_url = cls._resolve_generation_url(model_config)
        request_data = json.dumps(payload).encode('utf-8')
        req = Request(
            target_url,
            data=request_data,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with urlopen(req, timeout=120) as resp:
                response_bytes = resp.read()
        except HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
            raise ServiceException(message=f'图片生成失败: HTTP {e.code}, {error_body}') from e
        except URLError as e:
            raise ServiceException(message=f'图片生成失败: 无法连接图片服务, {e}') from e
        except Exception as e:
            raise ServiceException(message=f'图片生成失败: {e}') from e

        try:
            response_data = json.loads(response_bytes.decode('utf-8'))
        except Exception as e:
            raise ServiceException(message='图片生成失败: 上游返回了无法解析的响应') from e

        if not isinstance(response_data, dict):
            raise ServiceException(message='图片生成失败: 上游响应格式不正确')

        return response_data

    @classmethod
    def _extract_image_payload(cls, response: dict) -> tuple[str | None, str | None, str | None, str]:
        items = response.get('images') or response.get('data') or []
        if not isinstance(items, list) or not items:
            raise ServiceException(message=f'图片生成失败: 模型未返回图片数据, response={response}')

        item = items[0] or {}
        if not isinstance(item, dict):
            raise ServiceException(message='图片生成失败: 图片结果格式不正确')

        image_url = item.get('url') or item.get('image_url')
        revised_prompt = item.get('revised_prompt') or response.get('revised_prompt')
        mime_type = item.get('mime_type') or item.get('content_type') or 'image/png'
        image_data_url = None

        b64_json = item.get('b64_json') or item.get('b64') or item.get('base64')
        if b64_json:
            image_data_url = cls._build_data_url(b64_json, mime_type)
        elif image_url:
            image_data_url, mime_type = cls._download_image_as_data_url(image_url)

        return image_url, image_data_url, revised_prompt, mime_type

    @classmethod
    def _build_data_url(cls, base64_text: str, mime_type: str) -> str:
        return f'data:{mime_type};base64,{base64_text}'

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
