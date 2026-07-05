from datetime import datetime
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_ai.entity.vo.file_upload_vo import AiUploadResponseModel


class FileUploadService:
    """
    AI文件上传服务
    """

    @classmethod
    async def upload_to_files_temp(cls, file: UploadFile) -> CrudResponseModel:
        """
        上传文件到backend/FilesTemp目录

        :param file: 上传文件对象
        :return: 上传结果
        """
        if not file.filename:
            raise ServiceException(message='文件名不能为空')

        original_filename = Path(file.filename).name
        suffix = Path(original_filename).suffix
        stem = Path(original_filename).stem or 'file'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        new_file_name = f'{stem}_{timestamp}_{uuid4().hex[:8]}{suffix}'

        target_dir = Path(__file__).resolve().parents[2] / 'FilesTemp'
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / new_file_name

        async with aiofiles.open(target_path, 'wb') as f:
            while True:
                chunk = await file.read(1024 * 1024 * 10)
                if not chunk:
                    break
                await f.write(chunk)

        return CrudResponseModel(
            is_success=True,
            message='上传成功',
            result=AiUploadResponseModel(
                fileName=original_filename,
                newFileName=new_file_name,
                originalFilename=original_filename,
                storagePath=str(target_path),
            ),
        )
