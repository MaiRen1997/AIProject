import request from '@/utils/request'

const baseUrl = '/product_equipment'
// 查询产品组件列表
export function listProduct_equipment(query) {
  return request({
    url: baseUrl + '/list',
    method: 'get',
    params: query
  })
}

// 查询产品组件详细
export function getProduct_equipment(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'get'
  })
}

// 新增产品组件
export function addProduct_equipment(data) {
  return request({
    url: baseUrl,
    method: 'post',
    data: data
  })
}

// 修改产品组件
export function updateProduct_equipment(data) {
  return request({
    url: baseUrl,
    method: 'put',
    data: data
  })
}

// 删除产品组件
export function delProduct_equipment(id) {
  return request({
    url: baseUrl + '/' + id,
    method: 'delete'
  })
}
