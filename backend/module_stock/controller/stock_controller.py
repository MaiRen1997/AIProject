from typing import Dict, Any, List, Optional

import requests
from fastapi import Request, Query
from fastapi.responses import JSONResponse
from common.router import APIRouterPro
from module_stock.utils.commonFunction import formateDict, get_stock_detail_info

stock_controller = APIRouterPro(
    prefix='/stock',
    order_num=100,
    tags=['股票管理'],
)


@stock_controller.get(
    '/showDetailData',
    summary='获取股票详细数据',
    description='根据股票代码获取详细的历史数据和模拟交易结果',
)
async def show_detail_data(
    request: Request,
    code: Optional[str] = Query(None, description='股票代码'),
    sourceMoney: Optional[str] = Query(None, description='初始资金'),
) -> JSONResponse:
    temp_request = formateDict(dict(request.query_params))
    code = temp_request.get('code') or code
    if not code:
        return JSONResponse(status_code=400, content={
            'code': 400,
            'resultData': [],
            'message': '暂未输入股票代码'
        })

    base_money = temp_request.get('sourceMoney') or sourceMoney
    try:
        if base_money is None or base_money == '':
            base_money = 50000
        else:
            base_money = float(base_money)
    except Exception:
        base_money = 50000

    request_url = (
        'http://88.push2.eastmoney.com/api/qt/stock/kline/get?secid=1.' + code
        + "&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=1000000"
    )

    try:
        source_data = requests.get(request_url, timeout=10).json()
    except Exception as e:
        return JSONResponse(status_code=502, content={'code': 502, 'message': f'数据源请求失败: {e}', 'resultData': []})

    temp_data = source_data.get('data', {}).get('klines') or []
    result_data = []
    now_count = 0

    for itemData in temp_data:
        item = itemData.split(',')
        temp = {
            "time": item[0],
            "startPrice": item[1],
            "closePrice": item[2],
            "highestPrice": item[3],
            "lowestPrice": item[4],
            "raisePercent": item[8],
            "raisePrice": item[9],
            "countOfChange": float(item[5]) if item[5] != '' else 0.0,
            "countOfPrice": item[6],
            "range": item[7],
            "changePercent": item[10] if len(item) > 10 else '',
            "ratioChange": 0
        }
        result_data.append(temp)

    for index, item in enumerate(result_data):
        if index >= 5:
            denom = (
                result_data[index - 1]["countOfChange"] +
                result_data[index - 2]["countOfChange"] +
                result_data[index - 3]["countOfChange"] +
                result_data[index - 4]["countOfChange"] +
                result_data[index - 5]["countOfChange"]
            )
            try:
                item['ratioChange'] = round(item["countOfChange"] / denom, 2) if denom != 0 else 0
            except Exception:
                item['ratioChange'] = 0
        else:
            item['ratioChange'] = 0

    for index, item in enumerate(result_data):
        if 1 > float(item['ratioChange']) > 0 and float(item['raisePercent']) > 0 and base_money > 0 and now_count == 0:
            now_count = int(base_money // (float(item['closePrice']) * 100))
            item['testCount'] = now_count
            expend_money = now_count * float(item['closePrice']) * 100
            brokerage_temp = expend_money * 0.00025
            brokerage = brokerage_temp if brokerage_temp > 5 else 5
            transfer_ownership = expend_money * 0.00001
            base_money = base_money - expend_money - brokerage - transfer_ownership
        elif float(item['raisePercent']) <= 0 and now_count > 0:
            earn_money = float(now_count * float(item['closePrice']) * 100)
            brokerage_temp = earn_money * 0.00025
            brokerage = brokerage_temp if brokerage_temp > 5 else 5
            transfer_ownership = earn_money * 0.00001
            stamp_duty = earn_money * 0.001
            base_money = base_money + earn_money - brokerage - transfer_ownership - stamp_duty
            now_count = 0

        result_data[index]['base_money'] = base_money
        result_data[index]['now_count'] = now_count
        result_data[index]['value_money'] = base_money + now_count * 100 * float(item['closePrice'])

    return JSONResponse(status_code=200, content={
        'code': 200,
        'resultData': result_data,
    })


@stock_controller.get(
    '/filterStockWithHistoryFive',
    summary='筛选连续五天下跌的股票',
    description='查询当天上涨的股票，并筛选出过去五天（不含当天）连续下跌的股票',
)
def filter_stock_with_history_five() -> JSONResponse:
    if get_stock_detail_info is None:
        return JSONResponse(status_code=500, content={'code': 500, 'message': '依赖 get_stock_detail_info 未找到', 'resultData': []})

    request_url = (
        'http://6.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5440&po=1&np=1&'
        'ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&'
        'fs=m:1+t:2,m:1+t:23&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,'
        'f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
    )

    try:
        source_data = requests.get(request_url, timeout=10).json()
    except Exception as e:
        return JSONResponse(status_code=502, content={'code': 502, 'message': f'数据源请求失败: {e}', 'resultData': []})

    temp_data: List[Dict[str, Any]] = source_data.get('data', {}).get('diff') or []
    raise_data: List[Dict[str, Any]] = []

    for item in temp_data:
        try:
            if item.get('f3') != '-' and float(item.get('f3', 0)) > 0:
                raise_data.append(item)
        except Exception:
            continue

    history_data: List[Dict[str, Any]] = []
    for item in raise_data:
        symbol = str(item.get('f13', '')) + '.' + str(item.get('f12', ''))
        try:
            history_item = get_stock_detail_info(symbol)
        except Exception:
            continue

        flag = True
        detail_list = history_item.get('detail_info', [])
        for single in detail_list[0:-1]:
            parts = single.split(',')
            try:
                if float(parts[-3]) > 0:
                    flag = False
                    break
            except Exception:
                flag = False
                break

        if flag:
            history_data.append(history_item.get('stock_info'))

    return JSONResponse({
        'code': 200,
        'total': len(history_data),
        'resultData': history_data
    })


@stock_controller.get(
    '/getUptrendStock',
    summary='获取上涨趋势股票',
    description='查询当天上涨的股票，并筛选出成交量大于过去5天平均成交量的股票',
)
def get_uptrend_stock() -> JSONResponse:
    if get_stock_detail_info is None:
        return JSONResponse(status_code=500, content={'code': 500, 'message': '依赖 get_stock_detail_info 未找到', 'resultData': []})
    # 'http://6.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5440&po=1&np=1&'
    request_url = (
        'http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5440&po=1&np=1&'
        'ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&'
        'fs=m:1+t:2,m:1+t:23&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,'
        'f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
    )
    print('request_url', request_url)
    try:
        source_data = requests.get(request_url, timeout=10).json()
    except Exception as e:
        return JSONResponse(status_code=502, content={'code': 502, 'message': f'数据源请求失败: {e}', 'resultData': []})

    temp_data: List[Dict[str, Any]] = source_data.get('data', {}).get('diff') or []
    raise_data: List[Dict[str, Any]] = []
    for item in temp_data:
        try:
            if item.get('f3') != '-' and float(item.get('f3', 0)) > 0:
                raise_data.append(item)
        except Exception:
            continue

    history_data: List[Dict[str, Any]] = []
    for item in raise_data:
        symbol = str(item.get('f13', '')) + '.' + str(item.get('f12', ''))
        try:
            history_item = get_stock_detail_info(symbol)
        except Exception:
            continue

        range_five_exchange = 0
        for single in history_item.get('detail_info', [])[-6:-1]:
            temp = single.split(',')
            if temp and temp[-6] and temp[-6] != '-':
                try:
                    range_five_exchange += float(temp[-6])
                except Exception:
                    pass

        item['f5'] = 0 if item.get('f5') == '-' else item.get('f5')
        try:
            if float(item.get('f5', 0)) > float(range_five_exchange / 5):
                history_data.append({**item, 'rangeFiveExchange': range_five_exchange / 5, 'currentExchange': item.get('f5')})
        except Exception:
            continue

    return JSONResponse({
        'code': 200,
        'raiseData': raise_data,
        'tempData': temp_data,
        'resultData': history_data,
    })


@stock_controller.get(
    '/policyData',
    summary='获取股票政策数据',
    description='根据股票代码获取详细的历史数据',
)
def policy_data(code: Optional[str] = Query(None, description='股票代码')) -> JSONResponse:
    if get_stock_detail_info is None or formateDict is None:
        return JSONResponse(status_code=500, content={'code': 500, 'message': '依赖未找到', 'resultData': []})
    if not code:
        return JSONResponse(status_code=400, content={'code': 400, 'message': '缺少 code 参数', 'resultData': []})

    try:
        history_item = get_stock_detail_info(code)
    except Exception as e:
        return JSONResponse(status_code=502, content={'code': 502, 'message': f'获取历史信息失败: {e}', 'resultData': []})

    return JSONResponse({'code': 200, 'resultData': history_item})
