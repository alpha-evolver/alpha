#coding=utf-8
from __future__ import unicode_literals, division

import pandas as pd
import os

from alfe.reader.base_reader import AlfeFileNotFoundException, AlfeNotAssignVipdocPathException
from alfe.reader.base_reader import BaseReader
from collections import OrderedDict

"""
Legend from the internet...

2. TDX 5-minute line *.lc5 file and *.lc1 file, filename is stock code, every 32 bytes as one 5-minute data, each field has low byte first
00 ~ 01 bytes: Date, integer, set value as num, date calculation method: year=floor(num/2048)+2004; month=floor(mod(num,2048)/100); day=mod(mod(num,2048),100);
02 ~ 03 bytes: Minutes from 0:00 to now, integer
04 ~ 07 bytes: Open price, float
08 ~ 11 bytes: High price, float
12 ~ 15 bytes: Low price, float
16 ~ 19 bytes: Close price, float
20 ~ 23 bytes: Transaction amount, float
24 ~ 27 bytes: Transaction volume (shares), integer
28 ~ 31 bytes: (reserved)

After parsing with above method, float values are obviously not correct, so need to find another method

OHLC parse as integer, seems to match, divide by 100

Searched online again, seems this is the correct answer

http://www.ilovematlab.cn/thread-226577-1-1.html

Calculate, seems market index transaction volume data is not quite right, others seem fine, note transaction volume unit is not lots

"""



class AlfeMinBarReader(BaseReader):
    """
    Read TDX minute data
    """

    def parse_data_by_file(self, fname):
        if not os.path.isfile(fname):
            raise AlfeFileNotFoundException('no alfe kline data, please check path %s', fname)
        with open(fname, 'rb') as f:
            content = f.read()
            raw_li = self.unpack_records("<HHIIIIfII", content)
            data = []
            for row in raw_li:
                year, month, day = self._parse_date(row[0])
                hour, minute = self._parse_time(row[1])

                data.append(OrderedDict([
                    ("date", "%04d-%02d-%02d %02d:%02d" % (year, month, day, hour, minute)),
                    ("year", year),
                    ('month', month),
                    ('day', day),
                    ('hour', hour),
                    ('minute', minute),
                    ('open', row[2]/100),
                    ('high', row[3]/100),
                    ('low', row[4]/100),
                    ('close', row[5]/100),
                    ('amount', row[6]),
                    ('volume', row[7]),
                    #('unknown', row[8])
                ]))
            return data
        return []

    def get_df(self, code_or_file, exchange=None):
        #if exchange == None:
            # Only one parameter passed
        data = self.parse_data_by_file(code_or_file)
        #else:
        #    data = [self._df_convert(row) for row in self.get_kline_by_code(code_or_file, exchange)]
        df = pd.DataFrame(data=data)
        df.index = pd.to_datetime(df.date)
        return df[['open', 'high', 'low', 'close', 'amount', 'volume']]

    def _parse_date(self, num):
        year = num // 2048 + 2004
        month = (num % 2048) // 100
        day = (num % 2048) % 100

        return year, month, day

    def _parse_time(self, num):
        return (num // 60) , (num % 60)

if __name__ == '__main__':
    reader = AlfeMinBarReader()
    #df = reader.get_df("/Users/rainx/Downloads/sh000001.5")
    df = reader.get_df("/Users/rainx/Downloads/sh5fz/sh600000.5")
    print(df)

    print(df['2017-07-21'].sum())
