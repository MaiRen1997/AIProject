import request from '@/utils/request'

const baseUrl = '/product_info'
// 查询产品组件关联列表
export function listProduct_info(query) {
  return request({
    url: baseUrl + '/list',
    method: 'get',
    params: query
  })
}

// 查询产品组件关联详细
export function getProduct_info(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'get'
  })
}

// 新增产品组件关联
export function addProduct_info(data) {
  return request({
    url: baseUrl,
    method: 'post',
    data: data
  })
}

// 修改产品组件关联
export function updateProduct_info(data) {
  return request({
    url: baseUrl,
    method: 'put',
    data: data
  })
}

// 删除产品组件关联
export function delProduct_info(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'delete'
  })
}
