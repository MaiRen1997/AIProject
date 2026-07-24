import asyncio
import json
import mimetypes
import os
import re
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_ai.entity.vo.resume_filter_vo import (
    InterviewInviteRequestModel,
    InterviewInviteResultModel,
    ResumeOcrResultModel,
    ResumeScoreBreakdownModel,
    ResumeScoreRequestModel,
    ResumeScoreResultModel,
)


class ResumeFilterService:
    """简历筛选服务层"""

    @classmethod
    def _resume_file_dir(cls) -> Path:
        backend_dir = Path(__file__).resolve().parents[2]
        target_dir = backend_dir / 'FileTemp' / 'resumeFile'
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @classmethod
    async def upload_and_ocr_resume_services(cls, file: UploadFile) -> ResumeOcrResultModel:
        if not file.filename:
            raise ServiceException(message='文件名不能为空')

        raw_bytes = await file.read()
        if not raw_bytes:
            raise ServiceException(message='上传文件为空')

        original_filename = Path(file.filename).name
        suffix = Path(original_filename).suffix or '.bin'
        stem = Path(original_filename).stem or 'resume'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        saved_file_name = f'{stem}_{timestamp}_{uuid4().hex[:8]}{suffix}'

        target_path = cls._resume_file_dir() / saved_file_name
        await asyncio.to_thread(target_path.write_bytes, raw_bytes)

        ocr_text = await asyncio.to_thread(cls._ocr_recognize_sync, raw_bytes, original_filename)
        candidate_name, candidate_email, candidate_phone = cls._extract_candidate_fields(ocr_text)

        return ResumeOcrResultModel(
            file_name=original_filename,
            saved_file_name=saved_file_name,
            storage_path=str(target_path),
            ocr_text=ocr_text,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
        )

    @classmethod
    def _extract_candidate_fields(cls, ocr_text: str) -> tuple[str, str, str]:
        text = ocr_text or ''
        email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', text)
        phone_match = re.search(r'(?<!\d)(?:\+?86[-\s]?)?(1[3-9]\d{9})(?!\d)', text)

        name_patterns = [
            r'姓名\s*[:：]\s*([\u4e00-\u9fa5A-Za-z\s·]{2,30})',
            r'Name\s*[:：]\s*([\u4e00-\u9fa5A-Za-z\s·]{2,30})',
            r'候选人\s*[:：]\s*([\u4e00-\u9fa5A-Za-z\s·]{2,30})',
        ]
        candidate_name = ''
        for pattern in name_patterns:
            matched = re.search(pattern, text, flags=re.IGNORECASE)
            if matched:
                candidate_name = matched.group(1).strip()
                break

        if not candidate_name:
            for line in text.splitlines()[:12]:
                line_clean = line.strip()
                if not line_clean:
                    continue
                if '@' in line_clean or re.search(r'\d{6,}', line_clean):
                    continue
                if len(line_clean) > 24:
                    continue
                if re.search(r'[\u4e00-\u9fa5]{2,6}', line_clean):
                    candidate_name = line_clean
                    break

        candidate_email = email_match.group(1).strip() if email_match else ''
        candidate_phone = phone_match.group(1).strip() if phone_match else ''
        return candidate_name, candidate_email, candidate_phone

    @classmethod
    def _ocr_recognize_sync(cls, raw_bytes: bytes, original_filename: str) -> str:
        endpoint = os.getenv('RESUME_OCR_API_URL', '').strip() or 'https://api.ocr.space/parse/image'
        api_key = os.getenv('RESUME_OCR_API_KEY', '').strip() or os.getenv('OCR_SPACE_API_KEY', '').strip() or 'helloworld'

        mime_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        fields = {
            'apikey': api_key,
            'language': 'chs',
            'isOverlayRequired': 'false',
            'OCREngine': '2',
            'scale': 'true',
            'detectOrientation': 'true',
        }
        body, content_type = cls._build_multipart_body(fields, 'file', original_filename, raw_bytes, mime_type)

        req = Request(
            endpoint,
            data=body,
            headers={
                'Content-Type': content_type,
            },
            method='POST',
        )

        try:
            with urlopen(req, timeout=90) as resp:
                response_bytes = resp.read()
        except HTTPError as e:
            err_text = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
            raise ServiceException(message=f'OCR识别失败: HTTP {e.code}, {err_text}') from e
        except URLError as e:
            raise ServiceException(message=f'OCR识别失败: 无法连接识别服务, {e}') from e
        except Exception as e:
            raise ServiceException(message=f'OCR识别失败: {e}') from e

        try:
            payload = json.loads(response_bytes.decode('utf-8'))
        except Exception as e:
            raise ServiceException(message='OCR识别失败: 返回结果无法解析') from e

        if not isinstance(payload, dict):
            raise ServiceException(message='OCR识别失败: 返回格式不正确')

        if payload.get('IsErroredOnProcessing'):
            err = payload.get('ErrorMessage') or payload.get('ErrorDetails') or '上游OCR处理失败'
            if isinstance(err, list):
                err = '; '.join([str(x) for x in err])
            raise ServiceException(message=f'OCR识别失败: {err}')

        parsed_results = payload.get('ParsedResults') or []
        texts: list[str] = []
        for result in parsed_results:
            if not isinstance(result, dict):
                continue
            text = (result.get('ParsedText') or '').strip()
            if text:
                texts.append(text)

        return '\n'.join(texts).strip()

    @classmethod
    def _build_multipart_body(
        cls,
        fields: dict[str, str],
        file_field: str,
        file_name: str,
        file_bytes: bytes,
        content_type: str,
    ) -> tuple[bytes, str]:
        boundary = f'----ResumeBoundary{uuid4().hex}'
        lines: list[bytes] = []

        for key, value in fields.items():
            lines.append(f'--{boundary}'.encode('utf-8'))
            lines.append(f'Content-Disposition: form-data; name="{key}"'.encode('utf-8'))
            lines.append(b'')
            lines.append(str(value).encode('utf-8'))

        safe_file_name = Path(file_name).name
        lines.append(f'--{boundary}'.encode('utf-8'))
        lines.append(
            f'Content-Disposition: form-data; name="{file_field}"; filename="{safe_file_name}"'.encode('utf-8')
        )
        lines.append(f'Content-Type: {content_type}'.encode('utf-8'))
        lines.append(b'')
        lines.append(file_bytes)
        lines.append(f'--{boundary}--'.encode('utf-8'))
        lines.append(b'')

        body = b'\r\n'.join(lines)
        return body, f'multipart/form-data; boundary={boundary}'

    @classmethod
    async def score_resume_services(
        cls, query_db: AsyncSession, body: ResumeScoreRequestModel
    ) -> ResumeScoreResultModel:
        del query_db

        criteria = [
            {
                'criterion': item.criterion.strip(),
                'weight': float(item.weight),
            }
            for item in body.criteria
            if item.criterion.strip()
        ]
        if not criteria:
            raise ServiceException(message='至少需要一条有效筛选标准')

        payload = await asyncio.to_thread(cls._score_with_llm_sync, body.resume_text, criteria)
        score = cls._normalize_score(payload.get('score'))
        summary = str(payload.get('summary') or '').strip() or '模型未返回摘要'

        breakdown_data = payload.get('breakdown') if isinstance(payload.get('breakdown'), list) else []
        breakdown: list[ResumeScoreBreakdownModel] = []
        for item in breakdown_data:
            if not isinstance(item, dict):
                continue
            breakdown.append(
                ResumeScoreBreakdownModel(
                    criterion=str(item.get('criterion') or ''),
                    weight=float(item.get('weight') or 0),
                    score=float(item.get('score') or 0),
                    reason=str(item.get('reason') or ''),
                )
            )

        return ResumeScoreResultModel(score=score, summary=summary, breakdown=breakdown)

    @classmethod
    def _score_with_llm_sync(cls, resume_text: str, criteria: list[dict]) -> dict:
        api_key, base_url, model = cls._resolve_llm_config()
        url = cls._resolve_chat_completions_url(base_url)

        criteria_text = json.dumps(criteria, ensure_ascii=False)
        prompt = (
            '你是资深HR与技术面试官，请对候选人简历进行加权评分。\\n'
            '请严格输出JSON，不要输出其他文本。JSON结构如下：\\n'
            '{"score": 0-100数值, "summary": "总体评价", '
            '"breakdown": [{"criterion": "标准", "weight": 数值, "score": 0-100数值, "reason": "说明"}]}\\n\\n'
            '评分要求：\\n'
            '1) 综合分score范围0-100。\\n'
            '2) breakdown中的score是每条标准下的匹配分。\\n'
            '3) weight应与输入标准一致，可适度修正格式但不要改变含义。\\n\\n'
            f'【招聘标准与权重】\\n{criteria_text}\\n\\n'
            f'【候选人简历文本】\\n{resume_text}'
        )

        request_body = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': '你是简历筛选评分助手。输出必须是合法JSON对象。',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            'temperature': 0.2,
            'max_tokens': 1800,
        }

        req = Request(
            url,
            data=json.dumps(request_body, ensure_ascii=False).encode('utf-8'),
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
            err_text = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
            raise ServiceException(message=f'大模型评分失败: HTTP {e.code}, {err_text}') from e
        except URLError as e:
            raise ServiceException(message=f'大模型评分失败: 无法连接模型服务, {e}') from e
        except Exception as e:
            raise ServiceException(message=f'大模型评分失败: {e}') from e

        try:
            payload = json.loads(response_bytes.decode('utf-8'))
        except Exception as e:
            raise ServiceException(message='大模型评分失败: 上游返回无法解析') from e

        if not isinstance(payload, dict):
            raise ServiceException(message='大模型评分失败: 上游响应格式不正确')

        choices = payload.get('choices')
        if not isinstance(choices, list) or not choices:
            raise ServiceException(message=f'大模型评分失败: 未返回有效结果, response={payload}')

        message = choices[0].get('message') if isinstance(choices[0], dict) else None
        content = message.get('content') if isinstance(message, dict) else None
        if not content:
            raise ServiceException(message='大模型评分失败: 未返回内容')

        parsed = cls._parse_json_object_from_text(str(content))
        if not isinstance(parsed, dict):
            raise ServiceException(message='大模型评分失败: 返回内容不是合法JSON对象')

        return parsed

    @classmethod
    def _resolve_llm_config(cls) -> tuple[str, str, str]:
        api_key = (
            os.getenv('AI_RESUME_SCORE_API_KEY', '').strip()
            or os.getenv('OPENAI_API_KEY', '').strip()
            or os.getenv('DEEPSEEK_API_KEY', '').strip()
            or os.getenv('EMBEDDING_API_KEY', '').strip()
        )
        if not api_key:
            raise ServiceException(message='未配置大模型API Key，请设置 AI_RESUME_SCORE_API_KEY 或 OPENAI_API_KEY')

        base_url = (
            os.getenv('AI_RESUME_SCORE_BASE_URL', '').strip()
            or os.getenv('OPENAI_BASE_URL', '').strip()
            or os.getenv('DEEPSEEK_API_BASE_URL', '').strip()
            or 'https://api.deepseek.com/v1'
        )
        model = (
            os.getenv('AI_RESUME_SCORE_MODEL', '').strip()
            or os.getenv('OPENAI_CHAT_MODEL', '').strip()
            or os.getenv('DEEPSEEK_CHAT_MODEL', '').strip()
            or 'deepseek-chat'
        )
        return api_key, base_url, model

    @classmethod
    def _resolve_chat_completions_url(cls, base_url: str) -> str:
        normalized = (base_url or '').strip().rstrip('/')
        parsed = urlparse(normalized)
        path = parsed.path.rstrip('/')

        if path.endswith('/chat/completions'):
            return normalized
        if path.endswith('/v1'):
            return f'{normalized}/chat/completions'
        if '/v1/' in f'{path}/':
            base_root = normalized.split('/v1/', maxsplit=1)[0]
            return f'{base_root}/v1/chat/completions'
        return f'{normalized}/v1/chat/completions'

    @classmethod
    def _parse_json_object_from_text(cls, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        match = re.search(r'\{[\s\S]*\}', cleaned)
        if not match:
            raise ServiceException(message='大模型评分失败: 无法提取JSON内容')

        try:
            parsed = json.loads(match.group(0))
        except Exception as e:
            raise ServiceException(message='大模型评分失败: JSON解析异常') from e

        if not isinstance(parsed, dict):
            raise ServiceException(message='大模型评分失败: JSON结果不是对象')
        return parsed

    @classmethod
    def _normalize_score(cls, score: object) -> float:
        try:
            value = float(score)
        except Exception:
            value = 0.0
        if value < 0:
            value = 0.0
        if value > 100:
            value = 100.0
        return round(value, 2)

    @classmethod
    async def send_interview_invite_services(
        cls, query_db: AsyncSession, body: InterviewInviteRequestModel
    ) -> InterviewInviteResultModel:
        del query_db

        meeting_time = (body.meeting_time or '').strip()
        if not meeting_time:
            meeting_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 10:00')

        meeting_info = await asyncio.to_thread(
            cls._create_tencent_meeting_sync,
            body.job_name,
            body.hr_contact,
            meeting_time,
        )

        meeting_link = str(meeting_info.get('meeting_link') or '').strip()
        if not meeting_link:
            raise ServiceException(message='申请腾讯会议链接失败：未获取到会议链接')

        meeting_extra = str(meeting_info.get('meeting_extra_info') or '').strip()
        invite_message = (
            f'{body.candidate_name}你好，现邀请你参加{body.job_name}的面试，'
            f'会议时间{meeting_time}，会议链接{meeting_link}'
        )
        if meeting_extra:
            invite_message = f'{invite_message}，{meeting_extra}'
        invite_message = f'{invite_message}，请您准时参会'

        return InterviewInviteResultModel(
            meeting_time=meeting_time,
            meeting_link=meeting_link,
            meeting_extra_info=meeting_extra,
            invite_message=invite_message,
        )

    @classmethod
    def _create_tencent_meeting_sync(cls, job_name: str, hr_contact: str, meeting_time: str) -> dict:
        endpoint = os.getenv('TENCENT_MEETING_CREATE_URL', '').strip()
        api_token = os.getenv('TENCENT_MEETING_API_TOKEN', '').strip()
        auth_header = os.getenv('TENCENT_MEETING_AUTH_HEADER', '').strip() or 'Authorization'

        if not endpoint or not api_token:
            # 本地开发兜底：未配置腾讯会议开放平台参数时，生成模拟会议链接。
            fallback_link = f'https://meeting.tencent.com/dm/{uuid4().hex[:12]}'
            return {
                'meeting_link': fallback_link,
                'meeting_extra_info': f'HR联系方式：{hr_contact}',
            }

        payload = {
            'subject': f'{job_name} 面试邀约',
            'meeting_time': meeting_time,
            'hr_contact': hr_contact,
        }
        req = Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={
                auth_header: f'Bearer {api_token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with urlopen(req, timeout=45) as resp:
                response_bytes = resp.read()
        except HTTPError as e:
            err_text = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
            raise ServiceException(message=f'申请腾讯会议链接失败: HTTP {e.code}, {err_text}') from e
        except URLError as e:
            raise ServiceException(message=f'申请腾讯会议链接失败: 无法连接腾讯会议服务, {e}') from e
        except Exception as e:
            raise ServiceException(message=f'申请腾讯会议链接失败: {e}') from e

        try:
            result = json.loads(response_bytes.decode('utf-8'))
        except Exception as e:
            raise ServiceException(message='申请腾讯会议链接失败: 返回数据不可解析') from e

        if not isinstance(result, dict):
            raise ServiceException(message='申请腾讯会议链接失败: 返回格式不正确')

        data = result.get('data') if isinstance(result.get('data'), dict) else result
        meeting_link = (
            data.get('meeting_link')
            or data.get('join_url')
            or data.get('joinUrl')
            or data.get('meeting_url')
            or data.get('meetingUrl')
            or ''
        )
        meeting_id = data.get('meeting_id') or data.get('meetingId') or ''
        meeting_code = data.get('meeting_code') or data.get('meetingCode') or ''
        extra_parts = [f'HR联系方式：{hr_contact}']
        if meeting_id:
            extra_parts.append(f'会议ID：{meeting_id}')
        if meeting_code:
            extra_parts.append(f'入会码：{meeting_code}')

        return {
            'meeting_link': str(meeting_link).strip(),
            'meeting_extra_info': '，'.join(extra_parts),
        }
