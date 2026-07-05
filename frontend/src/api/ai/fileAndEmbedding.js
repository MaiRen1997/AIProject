import request from "@/utils/request";

export function uploadEmbeddingFile(data) {
  return request({
    url: "/ai/file/upload",
    method: "post",
    headers: { "Content-Type": "multipart/form-data" },
    data,
  });
}

export function listEmbeddingFiles() {
  return request({
    url: "/ai/embedding/files",
    method: "get",
  });
}

export function vectorizeEmbeddingFile(fileName) {
  return request({
    url: "/ai/embedding/vectorize",
    method: "post",
    data: {
      fileName,
    },
  });
}

export function queryEmbedding(question) {
  return request({
    url: "/ai/embedding/query",
    method: "post",
    data: {
      question,
    },
  });
}
