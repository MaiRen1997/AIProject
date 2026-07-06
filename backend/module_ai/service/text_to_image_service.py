import asyncio
import base64
import json
import mimetypes
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import urllib.request
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_ai.entity.vo.ai_model_vo import AiModelModel
from module_ai.entity.vo.text_to_image_vo import TextToImageRequestModel, TextToImageResultModel
class TextToImageService:
    """文生图服务层。"""

    @classmethod
    async def generate_image_services(
        cls, query_db: AsyncSession, request: TextToImageRequestModel
    ) -> TextToImageResultModel:
        del query_db
        model_config = cls._load_model_config(request.model_id)
        return await asyncio.to_thread(cls._generate_image_sync, model_config, request)

    @classmethod
    def _load_model_config(cls, model_id: int | None) -> AiModelModel:
        del model_id
        model_code = (
            os.getenv('AI_IMAGE_MODEL', '').strip()
            or os.getenv('TEXT_TO_IMAGE_MODEL', '').strip()
            or 'Kwai-Kolors/Kolors'
        )
        base_url = os.getenv('AI_IMAGE_BASE_URL', '').strip() or os.getenv('EMBEDDING_API_BASE_URL', '').strip()
        provider = os.getenv('AI_IMAGE_PROVIDER', '').strip() or 'SiliconFlow'

        if not model_code:
            raise ServiceException(message='环境变量 AI_IMAGE_MODEL/TEXT_TO_IMAGE_MODEL 未配置，无法调用图片生成服务')
        if not os.getenv('EMBEDDING_API_KEY', '').strip():
            raise ServiceException(message='环境变量 EMBEDDING_API_KEY 未配置，无法调用图片生成服务')

        return AiModelModel(
            modelId=None,
            modelCode=model_code,
            provider=provider,
            baseUrl=base_url,
            supportImages='Y',
            status='0',
        )

    @classmethod
    def _resolve_api_key(cls, model_config: AiModelModel) -> str:
        del model_config
        api_key = os.getenv('EMBEDDING_API_KEY', '').strip()
        if not api_key:
            raise ServiceException(message='环境变量 EMBEDDING_API_KEY 未配置，无法调用图片生成服务')
        return api_key

    @classmethod
    def _resolve_generation_url(cls, model_config: AiModelModel) -> str:
        base_url = (model_config.base_url or 'https://api.siliconflow.cn/v1').strip().rstrip('/')
        parsed = urlparse(base_url)
        path = parsed.path.rstrip('/')
        if path.endswith('/images/generations'):
            return base_url
        if path.endswith('/embeddings'):
            base_url = base_url[: -len('/embeddings')]
            path = urlparse(base_url).path.rstrip('/')
        if path.endswith('/v1'):
            return f'{base_url}/images/generations'
        if '/v1/' in f'{path}/':
            base_root = base_url.split('/v1/', maxsplit=1)[0]
            return f'{base_root}/v1/images/generations'
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

        extension = cls._resolve_download_extension(mime_type)
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
        mime_type = item.get('mime_type') or item.get('content_type') or 'image/jpeg'
        image_data_url = None

        b64_json = item.get('b64_json') or item.get('b64') or item.get('base64')
        if b64_json:
            image_data_url = cls._build_data_url(b64_json, mime_type)
        elif image_url:
            image_data_url, mime_type = cls._download_image_as_data_url(image_url)

        return image_url, image_data_url, revised_prompt, mime_type

    @classmethod
    def _resolve_download_extension(cls, mime_type: str) -> str:
        normalized = (mime_type or '').lower().strip()
        if not normalized or normalized == 'application/octet-stream':
            return '.jpg'

        if normalized in {'image/jpg', 'image/jpeg'}:
            return '.jpg'

        extension = mimetypes.guess_extension(normalized)
        if not extension or extension == '.bin':
            return '.jpg'
        return extension

    @classmethod
    def _build_data_url(cls, base64_text: str, mime_type: str) -> str:
        resolved_mime = mime_type if mime_type and mime_type != 'application/octet-stream' else 'image/jpeg'
        return f'data:{resolved_mime};base64,{base64_text}'

    @classmethod
    def _download_image_as_data_url(cls, image_url: str) -> tuple[str, str]:
        try:
            with urllib.request.urlopen(image_url, timeout=30) as resp:
                image_bytes = resp.read()
                mime_type = resp.headers.get_content_type() or 'image/jpeg'
        except Exception as e:
            raise ServiceException(message=f'图片已生成，但下载模型返回的图片链接失败: {e}') from e

        if mime_type == 'application/octet-stream':
            lower_url = (image_url or '').lower()
            if '.png' in lower_url:
                mime_type = 'image/png'
            elif '.webp' in lower_url:
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'

        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f'data:{mime_type};base64,{encoded}', mime_type
