import requests
import datetime
# 返回 量比小于1且涨幅大于0的数据
def findStockWithChangeOne():
    # 沪，京，深
    # request_url = 'http://6.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5440&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
    # 沪
    request_url = 'http://6.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5440&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&fs=m:1+t:2,m:1+t:23&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
    source_data = requests.get(request_url).json()
    temp_data = source_data['data']['diff'] or []
    result_data = []
    for item in temp_data:
        # if item['f3'] != '-' and item['f10'] != '-' and item['f3'] > 0 and item['f10'] < 0.5:
        if item['f3'] != '-' and item['f10'] != '-' and item['f3'] > 0 and item['f10'] < 1:
            result_data.append(item)
    return result_data


# 根据股票代码，查询5天历史价格，获取股票详情

def get_stock_detail_info(stock_sec_id):
    request_url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + stock_sec_id + '&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=1&end=20500101&lmt=6'
    source_data = requests.get(request_url).json()
    temp_data = source_data['data']['klines'] or []
    return {
        'stock_info': {
            'code': source_data['data']['code'],
            'name': source_data['data']['name']
        },
        'detail_info': temp_data
    }


# 根据股票代码，查询历史价格，以方便判断，是否主力已经开始拉升
def judgeIsRaised(stock_sec_id, lmt_count=20):
    request_url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&end=20500101&secid=' + stock_sec_id + '&klt=101&fqt=1&lmt="'+lmt_count+'"'
    source_data = requests.get(request_url).json()
    temp_data = source_data['data']['diff'] or []
    result_data = []
    for item in temp_data:
        if item['f3'] != '-' and item['f10'] != '-' and item['f3'] > 0 and item['f10'] < 0.5:
            result_data.append(item)
    return result_data
# 计算成交量
'''
默认获取10天的交易量
要求 10天内，交易量的波动幅度不超过10%， 并且红高，低矮
'''
def searchStochByCountOfChange(stockid, lmt='10'):
    request_url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + stockid + '&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=1&end=20500101&lmt='+lmt+'&_=1691162606748'
    result_data = []
    try:
        source_data = requests.get(request_url).json()
        temp_data = source_data['data']['klines'] or []
        for itemData in temp_data:
            item = itemData.split(',')
            temp = dict({
                "time": item[0],  # 时间
                "startPrice": float(item[1]),  # 开盘
                "closePrice": float(item[2]),  # 收盘
                "highestPrice": float(item[3]),  # 最高价
                "lowestPrice": float(item[4]),  # 最低价
                "countOfChange": float(item[5]),  # 成交量
                "countOfPrice": item[6],  # 成交额
                "range": item[7],  # 振幅
                "raisePercent": item[8],  # 涨跌幅
                "raisePrice": item[9],  # 涨跌额
                "changePercent": item[10],  # 换手率
                "ratioChange": 0
            })
            result_data.append(temp)
    except Exception as e:
        print(f"请求失败：{stockid}，错误信息：{e}")
    return result_data
# 模拟买入和卖出
def buyAndSale():
    request_url = 'http://88.push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.' + '688036' + '&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=1&end=20500101&lmt=1000000&_=1691162606748'
    # request_url = 'http://88.push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.' + '301299' + '&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=1&end=20500101&lmt=1000000&_=1691162606748'
    source_data = requests.get(request_url).json()
    temp_data = source_data['data']['klines'] or []
    result_data = []
    # 本金五万 进行操作
    # base_money = 10000
    base_money = 50000
    # 股票数 100股
    now_count = 0
    for itemData in temp_data:
        item = itemData.split(',')
        temp = dict({
            "time": item[0],  # 时间
            "startPrice": item[1],  # 开盘
            "closePrice": item[2],  # 收盘
            "highestPrice": item[3],  # 最高价
            "lowestPrice": item[4],  # 最低价
            "raisePercent": item[8],  # 涨跌幅
            "raisePrice": item[9],  # 涨跌额
            "countOfChange": float(item[5]),  # 成交量
            "countOfPrice": item[6],  # 成交额
            "range": item[7],  # 振幅
            "changePercent": item[10],  # 换手率
            "ratioChange": 0
        })
        result_data.append(temp)
    for index, item in enumerate(result_data):
        if index >= 5:
            item['ratioChange'] = round(item["countOfChange"] / (
                    result_data[index - 1]["countOfChange"] + result_data[index - 2]["countOfChange"] + result_data[
                index - 3]["countOfChange"] + result_data[index - 4]["countOfChange"] + result_data[
                        index - 5]["countOfChange"]), 2)
        else:
            item['ratioChange'] = 0
    for index, item in enumerate(result_data):
        '''
            佣金和过户费均是双向收取，印花税在卖出时收取
            佣金：成交金额*佣金费率(0.025%) 不足5收5
            过户费：成交金额*0.001%，买卖均收取
            印花税：成交金额*0.1%，卖出方收取
        '''
        if 1 > float(item['ratioChange']) > 0 and float(item['raisePercent']) > 0 and base_money > 0 and now_count == 0:
            now_count = base_money // (float(item['closePrice']) * 100)
            item['testCount'] = now_count
            # 买入所花费的资金
            expend_money = now_count * float(item['closePrice']) * 100
            # 佣金  约投入两万元，才不会触发最低5元的限制
            brokerage_temp = expend_money * 0.00025
            if brokerage_temp > 5:
                brokerage = brokerage_temp
            else:
                brokerage = 5
            # 过户费
            transfer_ownership = expend_money * 0.00001
            base_money = base_money - expend_money - brokerage - transfer_ownership
        # 关注股票，如果低于开盘价，就卖出
        elif float(item['raisePercent']) <= 0 and now_count > 0:  # 如果降了就抛出
            # 抛出所获得的资金
            earn_money = float(now_count * float(item['closePrice']) * 100)
            brokerage_temp = earn_money * 0.00025
            if brokerage_temp > 5:
                brokerage = brokerage_temp
            else:
                brokerage = 5
            # 过户费
            transfer_ownership = earn_money * 0.00001
            # 印花税
            stamp_duty = earn_money * 0.001
            base_money = base_money + earn_money - brokerage - transfer_ownership - stamp_duty
            now_count = 0
        result_data[index]['base_money'] = base_money
        result_data[index]['now_count'] = now_count
        result_data[index]['value_money'] = base_money + now_count * 100 * float(item['closePrice'])
    print('test', base_money)
    return result_data
def formateDict(val):
    search_dict = dict()
    for item in val:
        if val[item] or val[item] == 0:
            search_dict[item] = val[item]
    return search_dict


# 获取当前时间
def get_current_time(time_type="dateTime", join_code="-"):
    temp_stamp = datetime.datetime.now()
    year = str(temp_stamp.year)
    month = str(temp_stamp.month) if temp_stamp.month > 9 else '0' + str(temp_stamp.month)
    day = str(temp_stamp.day) if temp_stamp.day > 9 else '0' + str(temp_stamp.day)
    hour = str(temp_stamp.hour) if temp_stamp.hour > 9 else '0' + str(temp_stamp.hour)
    minute = str(temp_stamp.minute) if temp_stamp.minute > 9 else '0' + str(temp_stamp.minute)
    second = str(temp_stamp.second) if temp_stamp.second > 9 else '0' + str(temp_stamp.second)
    if time_type == 'date':
        return year + join_code + month + join_code + day
    if time_type == 'time':
        return hour + join_code + minute + join_code + second
    if time_type == 'dateTime':
        return year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second


# 转换字典
def formateDict(val):
    search_dict = dict()
    for item in val:
        if val[item] or val[item] ==0:
            search_dict[item] = val[item]
    return search_dict


# 数组转换成树状
def arrayToTree(val):
    temp = list(val)
    out = {
        0: {'menu_id': 0, 'pid': 0, 'name': "Root node", 'sub': []}
    }
    result = []
    menu_map = {}
    for item in temp:
        menu_map[item['menu_id']] = item
    for self in temp:
        if self['pid']:
            parent = menu_map[self['pid']]
            if 'children' not in parent:
                parent['children'] = []
            parent['children'].append(self)
            self['meta'] = {'title': self.get('title'), 'icon': self.get('icon'), 'noCache': True}
        else:
            self['component'] = 'Layout'
            self['alwaysShow'] = True
            self['hidden'] = False
            # self['name'] = self.get('title')
            self['path'] = '/' + self.get('path')
            self['meta'] = {'title': self.get('title'), 'icon': self.get('icon'), 'noCache': True}
            result.append(self)
    return result


def menuToTree(val):
    temp = list(val)
    out = {
        0: {'menu_id': 0, 'pid': 0, 'name': "Root node", 'sub': []}
    }
    result = []
    menu_map = {}
    for item in temp:
        menu_map[item['menu_id']] = item
    for self in temp:
        if self['pid']:
            parent = menu_map[self['pid']]
            if 'children' not in parent:
                parent['children'] = []
            parent['children'].append(self)
        else:
            result.append(self)
    return result