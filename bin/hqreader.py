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

# Let pandas display all data
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


Help_Text = '''
Data file format,
 - daily: Daily K-line
 - ex_daily: Extended market daily K-line
 - min: 5min or 1min K-line
 - lc: lc1, lc5 format minute K-line
 - gbbq: Share capital change file
 - block: Read sector stock list file
 - customblock: Read custom sector list
 - history_financial or hf: Historical financial info, e.g. gpcw20170930.dat or gpcw20170930.zip
'''

@click.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", '--output', help="")
@click.option("-d", "--datatype", default="daily", help=Help_Text)
def main(input, output, datatype):
    """
    TDX data file reader
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
            click.echo("Writing to file : " + output)
            df.to_csv(output)
        else:
            print(df)
    except Exception as e:
        print(str(e))

if __name__ == '__main__':
    main()
