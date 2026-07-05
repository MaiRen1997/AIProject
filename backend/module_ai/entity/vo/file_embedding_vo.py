from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class EmbeddingFileItemModel(BaseModel):
    """
    可向量化文件条目
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    file_name: str = Field(description='文件名')
    file_size: int = Field(description='文件大小（字节）')
    updated_at: str = Field(description='最后更新时间（ISO格式）')


class FileVectorizeRequestModel(BaseModel):
    """
    文件向量化请求模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    file_name: str = Field(description='文件名')


class FileVectorizeResultModel(BaseModel):
    """
    文件向量化结果模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    file_name: str = Field(description='文件名')
    chunk_count: int = Field(description='切块数量')
    inserted_count: int = Field(description='入库向量数量')
    collection_name: str = Field(description='向量集合名称')


class VectorQueryRequestModel(BaseModel):
    """
    向量查询请求模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(description='用户输入问题')


class VectorQueryHitModel(BaseModel):
    """
    向量命中片段模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    file_name: str = Field(description='来源文件名')
    chunk_index: int = Field(description='来源分块索引')
    score: float = Field(description='相似度分数')
    content: str = Field(description='分块内容')


class VectorQueryResultModel(BaseModel):
    """
    向量查询结果模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(description='用户问题')
    answer: str = Field(description='经过润色后的回答')
    matched_count: int = Field(description='命中文档数量')
    hits: list[VectorQueryHitModel] = Field(default_factory=list, description='命中片段')
