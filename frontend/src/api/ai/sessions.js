import request from '@/utils/request'

const baseUrl = '/sessions'
// 查询用户会话关联列表
export function listSessions(query) {
  return request({
    url: baseUrl + '/list',
    method: 'get',
    params: query
  })
}

// 查询用户会话关联详细
export function getSessions(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'get'
  })
}

// 新增用户会话关联
export function addSessions(data) {
  return request({
    url: baseUrl,
    method: 'post',
    data: data
  })
}

// 修改用户会话关联
export function updateSessions(data) {
  return request({
    url: baseUrl,
    method: 'put',
    data: data
  })
}

// 删除用户会话关联
export function delSessions(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'delete'
  })
}
