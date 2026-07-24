import request from '@/utils/request'

// givePriceChat: 根据用户输入提取产品并返回markdown表格
export function queryGivePriceChat(data) {
  return request({
    url: '/product_equipment/givePriceChat/query',
    method: 'post',
    data,
  })
}
