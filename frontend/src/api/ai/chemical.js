import request from "@/utils/request";

const baseURI = "/ai";

// 新建对话

// 获取会话列表
export function listChatSession() {
  return request({
    url: `${baseURI}/chat/session/list`,
    method: "get",
  });
}

// 删除会话
export function delChatSession(sessionId) {
  return request({
    url: `${baseURI}/chat/session/${sessionId}`,
    method: "delete",
  });
}

// 获取会话详情
export function getChatSession(sessionId) {
  return request({
    url: `${baseURI}/chat/session/${sessionId}`,
    method: "get",
  });
}

// 获取用户对话配置
export function getUserChatConfig() {
  return request({
    url: `${baseURI}/chat/config`,
    method: "get",
  });
}

// 保存用户对话配置
export function saveUserChatConfig(data) {
  return request({
    url: `${baseURI}/chat/config`,
    method: "put",
    data: data,
  });
}

// 取消对话
export function cancelChatRun(runId) {
  return request({
    url: `${baseURI}/chat/cancel`,
    method: "post",
    data: {
      runId: runId,
    },
  });
}
