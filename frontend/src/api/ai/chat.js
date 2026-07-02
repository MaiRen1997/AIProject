import request from "@/utils/request";

// 获取会话列表
export function listChatSession() {
  return request({
    url: "/ai/chat/session/list",
    method: "get",
  });
}

// 删除会话
export function delChatSession(sessionId) {
  return request({
    url: "/ai/chat/session/" + sessionId,
    method: "delete",
  });
}

// 获取会话详情
export function getChatSession(sessionId) {
  return request({
    url: "/ai/chat/session/" + sessionId,
    method: "get",
  });
}

// 获取用户对话配置
export function getUserChatConfig() {
  return request({
    url: "/ai/chat/config",
    method: "get",
  });
}

// 保存用户对话配置
export function saveUserChatConfig(data) {
  return request({
    url: "/ai/chat/config",
    method: "put",
    data: data,
  });
}

// 取消对话
export function cancelChatRun(runId) {
  return request({
    url: "/ai/chat/cancel",
    method: "post",
    data: {
      runId: runId,
    },
  });
}

// 接入人工客服
export function connectHumanSupport(data) {
  return request({
    url: "/ai/chat/human/connect",
    method: "post",
    data,
  });
}

// 发送人工客服消息
export function sendHumanSupportMessage(data) {
  return request({
    url: "/ai/chat/human/message",
    method: "post",
    data,
  });
}

// 获取人工客服状态
export function getHumanSupportStatus(sessionId) {
  return request({
    url: "/ai/chat/human/status/" + sessionId,
    method: "get",
  });
}
