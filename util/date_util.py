# coding:utf-8
from .trade_date import trade_date_sse

import datetime


def get_real_trade_date(date, towards):
    """
    Get the actual trading date. The third parameter 'towards' indicates forward/backward iteration.
    towards=1: date iterates forward
    towards=-1: date iterates backward
    @yutiansut
    """
    if towards == 1:
        while date not in trade_date_sse:
            date = str(datetime.datetime.strptime(
                date, '%Y-%m-%d') + datetime.timedelta(days=1))[0:10]
        else:
            return date
    elif towards == -1:
        while date not in trade_date_sse:
            date = str(datetime.datetime.strptime(
                date, '%Y-%m-%d') - datetime.timedelta(days=1))[0:10]
        else:
            return date
