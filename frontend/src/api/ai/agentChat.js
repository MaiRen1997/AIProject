/**和agent交互的接口 */
import request from "@/utils/request";
import { getToken } from "@/utils/auth";

const baseUrl = '/agent/'

// 非流式请求（保留）
export function chatWithAgent(data) {
  return request({
    url: baseUrl + "chat",
    method: "post",
    data: data,
  });
}

// 流式请求函数
export function chatWithAgentStream(data) {
  const url = import.meta.env.VITE_APP_BASE_API + baseUrl + "chat/stream"
  
  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + getToken(),
    },
    body: JSON.stringify(data),
  })
}
