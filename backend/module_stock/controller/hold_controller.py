from typing import Any, Dict
from fastapi import Request
from fastapi.responses import JSONResponse
from common.router import APIRouterPro

hold_controller = APIRouterPro(
    prefix='/stock',
    order_num=101,
    tags=['股票持仓管理'],
)


@hold_controller.get(
    '/holdStockData',
    summary='获取持仓股票数据',
    description='获取所有持仓股票数据',
)
def hold_stock_data() -> JSONResponse:
    return JSONResponse({'code': 200, 'resultData': []})


@hold_controller.post(
    '/holdStockData',
    summary='查询持仓股票',
    description='查询持仓股票数据',
)
def query_hold_stock() -> JSONResponse:
    return JSONResponse({'code': 200, 'resultData': []})


@hold_controller.put(
    '/holdStockData',
    summary='添加持仓股票',
    description='添加新的持仓股票',
)
async def add_hold_stock(request: Request) -> JSONResponse:
    return JSONResponse({'code': 200, 'resultData': []})


@hold_controller.delete(
    '/holdStockData',
    summary='删除持仓股票',
    description='删除指定的持仓股票',
)
async def delete_hold_stock(request: Request) -> JSONResponse:
    return JSONResponse({'code': 200, 'resultData': []})
