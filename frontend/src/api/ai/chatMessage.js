import request from '@/utils/request'

const baseUrl = '/chat_message'
// 查询聊天消息列表
export function listChat_message(query) {
  return request({
    url: baseUrl + '/list',
    method: 'get',
    params: query
  })
}

// 查询聊天消息详细
export function getChat_message(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'get'
  })
}

// 新增聊天消息
export function addChat_message(data) {
  return request({
    url: baseUrl,
    method: 'post',
    data: data
  })
}

// 修改聊天消息
export function updateChat_message(data) {
  return request({
    url: baseUrl,
    method: 'put',
    data: data
  })
}

// 删除聊天消息
export function delChat_message(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'delete'
  })
}
