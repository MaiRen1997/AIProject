import asyncio
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from exceptions.exception import ServiceException
from module_ai.entity.vo.file_embedding_vo import (
    EmbeddingFileItemModel,
    FileVectorizeResultModel,
    VectorQueryHitModel,
    VectorQueryResultModel,
)

@dataclass
class _SearchHit:
    file_name: str
    chunk_index: int
    content: str
    score: float


class FileEmbeddingService:
    """
    文件向量化服务
    """

    @classmethod
    def _files_temp_dir(cls) -> Path:
        backend_dir = Path(__file__).resolve().parents[2]
        file_temp_dir = backend_dir / 'FileTemp'
        files_temp_dir = backend_dir / 'FilesTemp'
        if file_temp_dir.exists():
            return file_temp_dir
        return files_temp_dir

    @classmethod
    def _sanitize_file_name(cls, file_name: str) -> str:
        safe_name = Path(file_name).name
        if safe_name != file_name:
            raise ServiceException(message='非法文件名')
        return safe_name

    @classmethod
    def _load_text(cls, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            raise ServiceException(message=f'读取文件失败: {e}') from e

    @classmethod
    def _split_chunks(cls, text: str) -> list[str]:
        chunk_size = int(os.getenv('AI_CHUNK_SIZE', '800'))
        overlap = int(os.getenv('AI_CHUNK_OVERLAP', '120'))
        cleaned = text.strip()
        if not cleaned:
            return []
        if chunk_size <= 0:
            chunk_size = 800
        if overlap < 0:
            overlap = 0
        if overlap >= chunk_size:
            overlap = min(120, chunk_size // 2)

        chunks: list[str] = []
        step = max(1, chunk_size - overlap)
        start = 0
        while start < len(cleaned):
            end = start + chunk_size
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += step
        return chunks

    @classmethod
    async def list_embedding_files(cls) -> list[EmbeddingFileItemModel]:
        target_dir = cls._files_temp_dir()
        target_dir.mkdir(parents=True, exist_ok=True)

        items: list[EmbeddingFileItemModel] = []
        for file in target_dir.iterdir():
            if not file.is_file():
                continue
            stat = file.stat()
            items.append(
                EmbeddingFileItemModel(
                    file_name=file.name,
                    file_size=stat.st_size,
                    updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                )
            )
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items

    @classmethod
    def _build_openai_client(cls):
        try:
            from openai import OpenAI
        except Exception as e:
            raise ServiceException(message='未安装 openai 依赖') from e

        api_key = os.getenv('OPENAI_API_KEY', '').strip() or os.getenv('DEEPSEEK_API_KEY', '').strip()
        if not api_key:
            raise ServiceException(message='缺少 OPENAI_API_KEY/DEEPSEEK_API_KEY，无法执行 embedding 与润色')

        base_url = os.getenv('OPENAI_BASE_URL', '').strip() or os.getenv('DEEPSEEK_API_BASE_URL', '').strip() or None
        return OpenAI(api_key=api_key, base_url=base_url)

    @classmethod
    def _build_embedding_client(cls):
        try:
            from openai import OpenAI
        except Exception as e:
            raise ServiceException(message='未安装 openai 依赖') from e

        # SiliconFlow embedding first; fall back to existing OpenAI-compatible vars.
        api_key = (
            os.getenv('EMBEDDING_API_KEY', '').strip()
            or os.getenv('SILICONFLOW_API_KEY', '').strip()
            or os.getenv('OPENAI_API_KEY', '').strip()
            or os.getenv('DEEPSEEK_API_KEY', '').strip()
        )
        if not api_key:
            raise ServiceException(message='缺少 EMBEDDING_API_KEY/SILICONFLOW_API_KEY/OPENAI_API_KEY，无法执行 embedding')

        raw_base_url = (
            os.getenv('SILICONFLOW_BASE_URL', '').strip()
            or os.getenv('EMBEDDING_API_BASE_URL', '').strip()
            or os.getenv('OPENAI_BASE_URL', '').strip()
            or 'https://api.siliconflow.cn/v1'
        )

        # OpenAI SDK expects base_url like .../v1, not .../v1/embeddings.
        base_url = raw_base_url[:-11] if raw_base_url.endswith('/embeddings') else raw_base_url
        return OpenAI(api_key=api_key, base_url=base_url)

    @classmethod
    def _embed_texts_sync(cls, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embedding_model = os.getenv('AI_EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-8B')
        embedding_encoding: Literal['float', 'base64'] = (
            'base64' if os.getenv('AI_EMBEDDING_ENCODING_FORMAT', 'float').strip() == 'base64' else 'float'
        )
        client = cls._build_embedding_client()
        try:
            resp = client.embeddings.create(
                model=embedding_model,
                input=texts,
                encoding_format=embedding_encoding,
            )
        except Exception as e:
            err_text = str(e)
            # Provider does not expose /embeddings or the configured model is invalid.
            if '404' in err_text:
                base_url = (
                    os.getenv('SILICONFLOW_BASE_URL', '').strip()
                    or os.getenv('EMBEDDING_API_BASE_URL', '').strip()
                    or os.getenv('OPENAI_BASE_URL', '').strip()
                    or 'https://api.siliconflow.cn/v1'
                )
                raise ServiceException(
                    message=(
                        'Embedding 服务返回404，请检查硅基流动地址与模型配置。'
                        f'当前 base_url={base_url}, model={embedding_model}'
                    )
                ) from e
            raise ServiceException(message=f'Embedding 调用失败: {err_text}') from e
        return [item.embedding for item in resp.data]

    @classmethod
    async def _embed_texts(cls, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(cls._embed_texts_sync, texts)

    @classmethod
    def _chroma_collection_name(cls) -> str:
        return os.getenv('CHROMA_COLLECTION_NAME', 'ai_file_embedding')

    @classmethod
    def _chroma_persist_dir(cls) -> str:
        configured = os.getenv('CHROMA_PERSIST_DIR', '').strip()
        if configured:
            return str(Path(configured).expanduser())
        backend_dir = Path(__file__).resolve().parents[2]
        return str(backend_dir / 'chroma_db')

    @classmethod
    def _get_chroma_collection_sync(cls):
        try:
            import chromadb
        except Exception as e:
            raise ServiceException(message='未安装 chromadb 依赖，请先安装 chromadb') from e

        persist_dir = cls._chroma_persist_dir()
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=persist_dir)
        return client.get_or_create_collection(
            name=cls._chroma_collection_name(),
            metadata={'hnsw:space': 'cosine'},
        )

    @classmethod
    def _insert_vectors_sync(cls, file_name: str, chunks: list[str], vectors: list[list[float]]) -> int:
        if not vectors:
            return 0
        if len(chunks) != len(vectors):
            raise ServiceException(message='分块数量与向量数量不一致，无法写入向量库')

        collection = cls._get_chroma_collection_sync()

        # 覆盖同名文件，避免重复向量残留。
        try:
            collection.delete(where={'file_name': file_name})
        except Exception:
            pass

        ids: list[str] = []
        metadatas: list[dict[str, object]] = []
        for idx, chunk in enumerate(chunks):
            digest = hashlib.sha1(f'{file_name}:{idx}:{chunk}'.encode('utf-8')).hexdigest()[:16]
            ids.append(f'{file_name}:{idx}:{digest}')
            metadatas.append({'file_name': file_name, 'chunk_index': idx})

        collection.upsert(ids=ids, documents=chunks, embeddings=vectors, metadatas=metadatas)
        return len(ids)

    @classmethod
    async def vectorize_file(cls, file_name: str) -> FileVectorizeResultModel:
        safe_name = cls._sanitize_file_name(file_name)
        file_path = cls._files_temp_dir() / safe_name
        if not file_path.exists() or not file_path.is_file():
            raise ServiceException(message='文件不存在')

        text = cls._load_text(file_path)
        chunks = cls._split_chunks(text)
        if not chunks:
            raise ServiceException(message='文件内容为空，无法向量化')

        vectors = await cls._embed_texts(chunks)
        inserted_count = await asyncio.to_thread(cls._insert_vectors_sync, safe_name, chunks, vectors)

        return FileVectorizeResultModel(
            file_name=safe_name,
            chunk_count=len(chunks),
            inserted_count=inserted_count,
            collection_name=cls._chroma_collection_name(),
        )

    @classmethod
    def _search_sync(cls, question_vector: list[float], top_k: int) -> list[_SearchHit]:
        collection = cls._get_chroma_collection_sync()
        if collection.count() == 0:
            return []

        search_result = collection.query(
            query_embeddings=[question_vector],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances'],
        )

        query_documents = (search_result.get('documents') or [[]])[0]
        query_metadatas = (search_result.get('metadatas') or [[]])[0]
        query_distances = (search_result.get('distances') or [[]])[0]

        hits: list[_SearchHit] = []
        for metadata, document, distance in zip(query_metadatas, query_documents, query_distances):
            metadata = metadata or {}
            cosine_distance = float(distance or 0.0)
            hits.append(
                _SearchHit(
                    file_name=str(metadata.get('file_name', '')),
                    chunk_index=int(metadata.get('chunk_index', 0)),
                    content=document or '',
                    score=max(0.0, 1.0 - cosine_distance),
                )
            )
        return hits

    @classmethod
    def _rerank_sync(cls, query: str, hits: list[_SearchHit], top_k: int) -> list[_SearchHit]:
        if not hits:
            return []

        api_key = os.getenv('COHERE_API_KEY', '').strip()
        rerank_model = os.getenv('AI_RERANK_MODEL', 'rerank-v3.5')
        if not api_key:
            return sorted(hits, key=lambda x: x.score, reverse=True)[:top_k]

        try:
            import cohere
        except Exception:
            return sorted(hits, key=lambda x: x.score, reverse=True)[:top_k]

        documents = [hit.content for hit in hits]
        client = cohere.ClientV2(api_key=api_key)
        rerank_resp = client.rerank(model=rerank_model, query=query, documents=documents, top_n=top_k)

        ordered_hits: list[_SearchHit] = []
        for item in rerank_resp.results:
            index = int(item.index)
            score = float(item.relevance_score)
            base_hit = hits[index]
            ordered_hits.append(
                _SearchHit(
                    file_name=base_hit.file_name,
                    chunk_index=base_hit.chunk_index,
                    content=base_hit.content,
                    score=score,
                )
            )
        return ordered_hits

    @classmethod
    def _polish_answer_sync(cls, question: str, reranked_hits: list[_SearchHit]) -> str:
        if not reranked_hits:
            return '未检索到足够相关的知识片段，请补充问题细节后重试。'

        llm_model = os.getenv('AI_CHAT_MODEL', 'gpt-4o-mini')
        client = cls._build_openai_client()

        context_blocks = []
        for idx, hit in enumerate(reranked_hits, start=1):
            context_blocks.append(
                f'[{idx}] 文件: {hit.file_name}, 分块: {hit.chunk_index}, 分数: {hit.score:.4f}\n{hit.content}'
            )
        context_text = '\n\n'.join(context_blocks)

        completion = client.chat.completions.create(
            model=llm_model,
            temperature=0.2,
            messages=[
                {
                    'role': 'system',
                    'content': '你是企业知识库问答助手。请根据提供的检索片段生成准确、简洁、中文回答。若证据不足请明确说明。',
                },
                {
                    'role': 'user',
                    'content': f'用户问题:\n{question}\n\n检索片段:\n{context_text}',
                },
            ],
        )
        return completion.choices[0].message.content or ''

    @classmethod
    async def query_and_generate(cls, question: str) -> VectorQueryResultModel:
        q = question.strip()
        if not q:
            raise ServiceException(message='问题不能为空')

        question_vec = (await cls._embed_texts([q]))[0]
        searched_hits = await asyncio.to_thread(cls._search_sync, question_vec, 10)
        reranked_hits = await asyncio.to_thread(cls._rerank_sync, q, searched_hits, 10)
        polished_text = await asyncio.to_thread(cls._polish_answer_sync, q, reranked_hits)

        return VectorQueryResultModel(
            question=q,
            answer=polished_text,
            matched_count=len(reranked_hits),
            hits=[
                VectorQueryHitModel(
                    file_name=hit.file_name,
                    chunk_index=hit.chunk_index,
                    score=hit.score,
                    content=hit.content,
                )
                for hit in reranked_hits
            ],
        )
