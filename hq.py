# coding=utf-8

#
# Just for practising
#


import datetime
import os
import random
import socket
import sys
import threading

import pandas as pd
from alfe.base_socket_client import BaseSocketClient, update_last_ack_time
from alfe.heartbeat import HqHeartBeatThread
from alfe.log import DEBUG, log
from alfe.params import ALFEParams
from alfe.parser.get_block_info import (GetBlockInfo, GetBlockInfoMeta,
                                         get_and_parse_block_info)
from alfe.parser.get_company_info_category import GetCompanyInfoCategory
from alfe.parser.get_company_info_content import GetCompanyInfoContent
from alfe.parser.get_finance_info import GetFinanceInfo
from alfe.parser.get_history_minute_time_data import GetHistoryMinuteTimeData
from alfe.parser.get_history_transaction_data import GetHistoryTransactionData
from alfe.parser.get_index_bars import GetIndexBarsCmd
from alfe.parser.get_minute_time_data import GetMinuteTimeData
from alfe.parser.get_security_bars import GetSecurityBarsCmd
from alfe.parser.get_security_count import GetSecurityCountCmd
from alfe.parser.get_security_list import GetSecurityList
from alfe.parser.get_security_quotes import GetSecurityQuotesCmd
from alfe.parser.get_transaction_data import GetTransactionData
from alfe.parser.get_xdxr_info import GetXdXrInfo
from alfe.parser.get_report_file import GetReportFile
from alfe.parser.setup_commands import SetupCmd1, SetupCmd2, SetupCmd3
from alfe.util import get_real_trade_date, trade_date_sse
try:
    # Python 3
    from collections.abc import Iterable
except ImportError:
    # Python 2.7
    from collections import Iterable

if __name__ == '__main__':
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.realpath(__file__))))


class AlfeHq_API(BaseSocketClient):

    def setup(self):
        SetupCmd1(self.client).call_api()
        SetupCmd2(self.client).call_api()
        SetupCmd3(self.client).call_api()

    # API List

    # Note: If a stock is suspended on a trading day, the K-line for that day can still be retrieved, with volume = 0
    @update_last_ack_time
    def get_security_bars(self, category, market, code, start, count):
        cmd = GetSecurityBarsCmd(self.client, lock=self.lock)
        cmd.setParams(category, market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_index_bars(self, category, market, code, start, count):
        cmd = GetIndexBarsCmd(self.client, lock=self.lock)
        cmd.setParams(category, market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_quotes(self, all_stock, code=None):
        """
        Supports three forms of parameters:
        get_security_quotes(market, code )
        get_security_quotes((market, code))
        get_security_quotes([(market1, code1), (market2, code2)] )
        :param all_stock: array of (market, code)
        :param code{optional}: code to query
        :return:
        """

        if code is not None:
            all_stock = [(all_stock, code)]
        elif (isinstance(all_stock, list) or isinstance(all_stock, tuple))\
                and len(all_stock) == 2 and type(all_stock[0]) is int:
            all_stock = [all_stock]

        cmd = GetSecurityQuotesCmd(self.client, lock=self.lock)
        cmd.setParams(all_stock)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_count(self, market):
        cmd = GetSecurityCountCmd(self.client, lock=self.lock)
        cmd.setParams(market)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_list(self, market, start):
        cmd = GetSecurityList(self.client, lock=self.lock)
        cmd.setParams(market, start)
        return cmd.call_api()

    @update_last_ack_time
    def get_minute_time_data(self, market, code):
        cmd = GetMinuteTimeData(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_history_minute_time_data(self, market, code, date):
        cmd = GetHistoryMinuteTimeData(self.client, lock=self.lock)
        cmd.setParams(market, code, date)
        return cmd.call_api()

    @update_last_ack_time
    def get_transaction_data(self, market, code, start, count):
        cmd = GetTransactionData(self.client, lock=self.lock)
        cmd.setParams(market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_history_transaction_data(self, market, code, start, count, date):
        cmd = GetHistoryTransactionData(self.client, lock=self.lock)
        cmd.setParams(market, code, start, count, date)
        return cmd.call_api()

    @update_last_ack_time
    def get_company_info_category(self, market, code):
        cmd = GetCompanyInfoCategory(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_company_info_content(self, market, code, filename, start, length):
        cmd = GetCompanyInfoContent(self.client, lock=self.lock)
        cmd.setParams(market, code, filename, start, length)
        return cmd.call_api()

    @update_last_ack_time
    def get_xdxr_info(self, market, code):
        cmd = GetXdXrInfo(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_finance_info(self, market, code):
        cmd = GetFinanceInfo(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_block_info_meta(self, blockfile):
        cmd = GetBlockInfoMeta(self.client, lock=self.lock)
        cmd.setParams(blockfile)
        return cmd.call_api()

    @update_last_ack_time
    def get_block_info(self, blockfile, start, size):
        cmd = GetBlockInfo(self.client, lock=self.lock)
        cmd.setParams(blockfile, start, size)
        return cmd.call_api()

    def get_and_parse_block_info(self, blockfile):
        return get_and_parse_block_info(self, blockfile)

    @update_last_ack_time
    def get_report_file(self, filename, offset):
        cmd = GetReportFile(self.client, lock=self.lock)
        cmd.setParams(filename, offset)
        return cmd.call_api()

    def get_report_file_by_size(self, filename, filesize=0, reporthook=None):
        """
        Download file from proxy server

        :param filename: the filename to download
        :param filesize: the filesize to download, if you do not know the actual filesize, leave this value 0
        """
        filecontent = bytearray(filesize)
        current_downloaded_size = 0
        get_zero_length_package_times = 0
        while current_downloaded_size < filesize or filesize == 0:
            response = self.get_report_file(filename, current_downloaded_size)
            if response["chunksize"] > 0:
                current_downloaded_size = current_downloaded_size + \
                    response["chunksize"]
                filecontent.extend(response["chunkdata"])
                if reporthook is not None:
                    reporthook(current_downloaded_size,filesize)
            else:
                get_zero_length_package_times = get_zero_length_package_times + 1
                if filesize == 0:
                    break
                elif get_zero_length_package_times > 2:
                    break

        return filecontent

    def do_heartbeat(self):
        self.get_security_count(random.randint(0, 1))

    def get_k_data(self, code, start_date, end_date):
        # For details, see https://github.com/alpha-evolver/alfe/issues/5
        # For details, see https://github.com/alpha-evolver/alfe/issues/21
        def __select_market_code(code):
            code = str(code)
            if code[0] in ['5', '6', '9'] or code[:3] in ["009", "126", "110", "201", "202", "203", "204"]:
                return 1
            return 0
        # New lazy one-size-fits-all approach zzz
        market_code = 1 if str(code)[0] == '6' else 0
        # https://github.com/alpha-evolver/alfe/issues/33
        # 0 - Shenzhen, 1 - Shanghai

        data = pd.concat([self.to_df(self.get_security_bars(9, __select_market_code(
            code), code, (9 - i) * 800, 800)) for i in range(10)], axis=0)

        data = data.assign(date=data['datetime'].apply(lambda x: str(x)[0:10])).assign(code=str(code))\
            .set_index('date', drop=False, inplace=False)\
            .drop(['year', 'month', 'day', 'hour', 'minute', 'datetime'], axis=1)[start_date:end_date]
        return data.assign(date=data['date'].apply(lambda x: str(x)[0:10]))


if __name__ == '__main__':
    import pprint

    api = AlfeHq_API()
    if api.connect('101.227.73.20', 7709):
        log.info("Get stock quotes")
        stocks = api.get_security_quotes([(0, "000001"), (1, "600300")])
        pprint.pprint(stocks)
        log.info("Get K-lines")
        data = api.get_security_bars(9, 0, '000001', 4, 3)
        pprint.pprint(data)
        log.info("Get Shenzhen stock count")
        pprint.pprint(api.get_security_count(0))
        log.info("Get stock list")
        stocks = api.get_security_list(1, 255)
        pprint.pprint(stocks)
        log.info("Get index K-lines")
        data = api.get_index_bars(9, 1, '000001', 1, 2)
        pprint.pprint(data)
        log.info("Query intraday quotes")
        data = api.get_minute_time_data(ALFEParams.MARKET_SH, '600300')
        pprint.pprint(data)
        log.info("Query historical intraday quotes")
        data = api.get_history_minute_time_data(
            ALFEParams.MARKET_SH, '600300', 20161209)
        pprint.pprint(data)
        log.info("Query intraday transactions")
        data = api.get_transaction_data(ALFEParams.MARKET_SZ, '000001', 0, 30)
        pprint.pprint(data)
        log.info("Query historical intraday transactions")
        data = api.get_history_transaction_data(
            ALFEParams.MARKET_SZ, '000001', 0, 10, 20170209)
        pprint.pprint(data)
        log.info("Query company info category")
        data = api.get_company_info_category(ALFEParams.MARKET_SZ, '000001')
        pprint.pprint(data)
        log.info("Read company info - latest notes")
        data = api.get_company_info_content(0, '000001', '000001.txt', 0, 10)
        pprint.pprint(data)
        log.info("Read ex-rights/ex-dividend info")
        data = api.get_xdxr_info(1, '600300')
        pprint.pprint(data)
        log.info("Read financial info")
        data = api.get_finance_info(0, '000001')
        pprint.pprint(data)
        log.info("Daily K-line fetch function")
        data = api.get_k_data('000001', '2017-07-01', '2017-07-10')
        pprint.pprint(data)

        api.disconnect()
