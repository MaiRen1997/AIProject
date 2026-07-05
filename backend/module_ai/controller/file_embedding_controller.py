from fastapi import Request, Response

from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_ai.entity.vo.file_embedding_vo import (
    EmbeddingFileItemModel,
    FileVectorizeRequestModel,
    FileVectorizeResultModel,
    VectorQueryRequestModel,
    VectorQueryResultModel,
)
from module_ai.service.file_embedding_service import FileEmbeddingService
from utils.log_util import logger
from utils.response_util import ResponseUtil

file_embedding_controller = APIRouterPro(
    prefix='/ai/embedding', order_num=24, tags=['AI管理-文件向量化'], dependencies=[PreAuthDependency()]
)


@file_embedding_controller.get(
    '/files',
    summary='获取可向量化文件列表',
    description='返回 backend/FileTemp 或 backend/FilesTemp 下的文件列表',
    response_model=DataResponseModel[list[EmbeddingFileItemModel]],
)
async def get_embedding_files(request: Request) -> Response:
    files = await FileEmbeddingService.list_embedding_files()
    logger.info(f'获取文件列表成功，数量: {len(files)}')
    return ResponseUtil.success(data=files)


@file_embedding_controller.post(
    '/vectorize',
    summary='文件向量化并写入ChromaDB',
    description='加载文件并切块后完成向量化，最终写入ChromaDB',
    response_model=DataResponseModel[FileVectorizeResultModel],
)
async def vectorize_file(request: Request, body: FileVectorizeRequestModel) -> Response:
    result = await FileEmbeddingService.vectorize_file(body.file_name)
    logger.info(f'文件向量化成功: {result.file_name}, chunk={result.chunk_count}, inserted={result.inserted_count}')
    return ResponseUtil.success(data=result)


@file_embedding_controller.post(
    '/query',
    summary='向量查询与AI润色回答',
    description='问题向量化后检索ChromaDB，rerank排序后由LLM生成润色回答',
    response_model=DataResponseModel[VectorQueryResultModel],
)
async def query_embedding(request: Request, body: VectorQueryRequestModel) -> Response:
    result = await FileEmbeddingService.query_and_generate(body.question)
    logger.info(f'向量问答完成，命中数量: {result.matched_count}')
    return ResponseUtil.success(data=result)
