# coding=utf-8

from alfe.parser.base import BaseParser
from alfe.helper import get_datetime, get_volume, get_price
from collections import OrderedDict
import struct
import datetime

class GetHistoryTransactionData(BaseParser):

    def setParams(self, market, code, date, start, count):
        # if type(code) is six.text_type:
        code = code.encode("utf-8")

        # if type(date) is (type(date) is six.text_type) or (type(date) is six.binary_type):
        #     date = int(date)

        # pkg1 = bytearray.fromhex('01 01 30 00 02 01 16 00 16 00 06 24 3b c8 33 01 1f 30 30 30 32 30 00 00 00 01 00 00 00 00 f0 00')
        pkg = bytearray.fromhex('01 01 30 00 02 01 16 00 16 00 06 24')
        pkg.extend(struct.pack("<IB9siH", date, market, code, start, count))
        self.send_pkg = pkg
        self.date = date

    def parseResponse(self, body_buf):

        pos = 0
        market, code, _, num = struct.unpack('<B9s4sH', body_buf[pos: pos + 16])
        pos += 16
        result = []
        for i in range(num):

            (raw_time, price, volume, zengcang, direction) = struct.unpack("<HIIiH", body_buf[pos: pos + 16])

            pos += 16
            year = self.date // 10000
            month = self.date % 10000 // 100
            day = self.date % 100
            hour = raw_time // 60
            minute = raw_time % 60
            second = direction % 10000
            nature = direction #### For compatibility with old user interface, already converted to use nature_value
            value = direction // 10000
            # For values greater than 59 seconds, it's an invalid value
            if second > 59:
                second = 0
            date = datetime.datetime(year, month, day, hour, minute, second)

            if value == 0:
                direction = 1
                if zengcang > 0:
                    if volume > zengcang:
                        nature_name = "Long Open"
                    elif volume == zengcang:
                        nature_name = "Double Open"
                elif zengcang == 0:
                    nature_name = "Long Switch"
                else:
                    if volume == -zengcang:
                        nature_name = "Double Close"
                    else:
                        nature_name = "Short Close"
            elif value == 1:
                direction = -1
                if zengcang > 0:
                    if volume > zengcang:
                        nature_name = "Short Open"
                    elif volume == zengcang:
                        nature_name = "Double Open"
                elif zengcang == 0:
                    nature_name = "Short Switch"
                else:
                    if volume == -zengcang:
                        nature_name = "Double Close"
                    else:
                        nature_name = "Long Close"
            else:
                direction = 0
                if zengcang > 0:
                    if volume > zengcang:
                        nature_name = "Open Position"
                    elif volume == zengcang:
                        nature_name = "Double Open"
                elif zengcang < 0:
                    if volume > -zengcang:
                        nature_name = "Close Position"
                    elif volume == -zengcang:
                        nature_name = "Double Close"
                else:
                    nature_name = "Switch"

            if market in [31,48]:
                if nature == 0:
                    direction = 1
                    nature_name = 'B'
                elif nature == 256:
                    direction = -1
                    nature_name = 'S'
                else: #512
                    direction = 0
                    nature_name = ''

            result.append(OrderedDict([
                ("date", date),
                ("hour", hour),
                ("minute", minute),
                ("price", price),
                ("volume", volume),
                ("zengcang", zengcang),
                ("natrue_name", nature_name),
                ("nature_name", nature_name), #Fix nature_name spelling error (natrue), to maintain compatibility, original natrue_name will be kept for a period of time
                ("direction", direction),
                ("nature", nature),

            ]))

        return result


if __name__ == '__main__':

    from alfe.exhq import AlfeExHq_API

    api = AlfeExHq_API()
    with api.connect('121.14.110.210', 7727):
        # print(api.to_df(api.get_history_transaction_data(4, 'SR61099D', 20171025))[["date","price","volume",'zengcang','nature','t1','t2']])

        print(api.to_df(api.get_history_transaction_data(47, 'IFL0', 20170811)))
        #print(api.to_df(api.get_history_transaction_data(31,  "01918", 20171026))[["date","price","volume",'zengcang','nature']])
        #api.to_df(api.get_history_transaction_data(47, 'IFL0', 20170810)).to_excel('//Users//wy//data//iflo.xlsx')