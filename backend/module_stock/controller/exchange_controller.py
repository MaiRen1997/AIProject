from typing import List, Dict, Any
import time
import random
import importlib
import requests
from fastapi.responses import JSONResponse
from common.router import APIRouterPro

exchange_controller = APIRouterPro(
    prefix='/stock',
    order_num=102,
    tags=['股票换手率分析'],
)

try:
    _mod = importlib.import_module('module_stock.utils.commonFunction')
    searchStochByCountOfChange = getattr(_mod, 'searchStochByCountOfChange')
except Exception:
    searchStochByCountOfChange = None


@exchange_controller.get(
    '/getExchangedStock',
    summary='获取换手率分析股票',
    description='获取换手率符合特定条件的股票列表',
)
def get_exchanged_stock() -> JSONResponse:
    if searchStochByCountOfChange is None:
        return JSONResponse(status_code=500, content={'code': 500, 'message': '依赖 searchStochByCountOfChange 未找到', 'resultData': []})

    all_stocks: List[Dict[str, Any]] = []
    page = 1
    page_size = 100
    while True:
        request_url = (
            'http://6.push2.eastmoney.com/api/qt/clist/get?pn=' + str(page)
            + ' &pz=' + str(page_size)
            + "&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&fs=m:1+t:2+f:!50&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152"
        )
        try:
            data = requests.get(request_url, timeout=10).json()
        except Exception:
            break
        if not data.get('data'):
            break
        items = data['data'].get('diff') or []
        if not items:
            break
        for item in items:
            all_stocks.append(item)
        page += 1

    time.sleep(random.uniform(0.5, 1.5))

    stock_array: List[Dict[str, Any]] = []
    sample_length = 300
    for index, item in enumerate(all_stocks[0:sample_length]):
        history_item = searchStochByCountOfChange(str(item.get('f13', '')) + '.' + str(item.get('f12', '')), '11')
        if not history_item:
            continue
        try:
            current_data = history_item.pop()
        except Exception:
            continue

        if not history_item or len(history_item) < 10:
            stock_array = []
        else:
            base_exchange = history_item[0].get('countOfChange')
            min_stand = base_exchange * 0.8
            max_stand = base_exchange * 1.2
            single = history_item[9]
            if (
                min_stand < single.get('countOfChange') < max_stand
                and single.get('lowestPrice') > single.get('startPrice') * 0.99
                and single.get('closePrice') < single.get('highestPrice')
            ):
                stock_array.append({
                    'stock_code': item.get('f12'),
                    'stock_name': item.get('f14'),
                    'history_data': history_item
                })

        time.sleep(random.uniform(0.5, 1.5))

    return JSONResponse({
        'code': 200,
        'resultData': stock_array,
        'length': len(stock_array)
    })
