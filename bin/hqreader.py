#coding=utf-8
from __future__ import unicode_literals, division
import click
import sys
import os
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from alfe.reader import AlfeDailyBarReader, AlfeFileNotFoundException, AlfeNotAssignVipdocPathException
from alfe.reader import AlfeMinBarReader
from alfe.reader import AlfeLCMinBarReader
from alfe.reader import AlfeExHqDailyBarReader
from alfe.reader import GbbqReader
from alfe.reader import BlockReader
from alfe.reader import CustomerBlockReader
from alfe.reader.history_financial_reader import HistoryFinancialReader
import pandas as pd

# 让pandas 显示全部数据
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


Help_Text = '''
数据文件格式，
 - daily 代表日K线
 - ex_daily 代表扩展行情的日线
 - min 代表5分钟或者1分钟线
 - lc 代表lc1, lc5格式的分钟线
 - gbbq 股本变迁文件
 - block 读取板块股票列表文件
 - customblock 读取自定义板块列表
 - history_financial 或者 hf 历史财务信息 如 gpcw20170930.dat 或者 gpcw20170930.zip
'''

@click.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", '--output', help="")
@click.option("-d", "--datatype", default="daily", help=Help_Text)
def main(input, output, datatype):
    """
    通达信数据文件读取
    """

    if datatype == 'daily':
        reader = AlfeDailyBarReader()
    elif datatype == 'ex_daily':
        reader = AlfeExHqDailyBarReader()
    elif datatype == 'lc':
        reader = AlfeLCMinBarReader()
    elif datatype == 'gbbq':
        reader = GbbqReader()
    elif datatype == 'block':
        reader = BlockReader()
    elif datatype == 'customblock':
        reader = CustomerBlockReader()
    elif datatype == 'history_financial' or datatype == 'hf':
        reader = HistoryFinancialReader()
    else:
        reader = AlfeMinBarReader()

    try:
        df = reader.get_df(input)
        if output:
            click.echo("写入到文件 : " + output)
            df.to_csv(output)
        else:
            print(df)
    except Exception as e:
        print(str(e))

if __name__ == '__main__':
    main()