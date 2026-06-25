/**和会话相关的接口 */
import request from "@/utils/request";

const BaseUrl = "/session/"
// 获取会话列表
export function generateSessionID() {
  return request({
    url: BaseUrl + "generateSessionID",
    method: "get",
  });
}