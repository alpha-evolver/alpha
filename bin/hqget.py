# coding=utf-8
from __future__ import unicode_literals

import os
import sys
import click

from collections import OrderedDict
import pprint

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from alfe.hq import AlfeHq_API
from alfe.params import ALFEParams
from alfe.config.hosts import hq_hosts
import pandas as pd
import pickle
from functools import reduce


# Let pandas display all data
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

mtstr = os.getenv("ALFE_MT", "")
mt = False
if mtstr:
    mt = True

api = AlfeHq_API(multithread=mt)


def get_security_quotes(params):
    market, code = params
    stocks = api.get_security_quotes([(int(market), code),])
    return (stocks)

def get_security_bars(params):
    category, market, code, start, count = params
    return (api.get_security_bars(int(category), int(market), code, int(start), int(count)))

def get_security_count(params):
    return (api.get_security_count(int(params[0])))

def get_security_list(params):
    return (api.get_security_list(int(params[0]), int(params[1])))

def get_index_bars(params):
    category, market, code, start, count = params
    return (api.get_index_bars(int(category), int(market), code, int(start), int(count)))

def get_minute_time_data(params):
    return (api.get_minute_time_data(int(params[0]), params[1]))

def get_history_minute_time_data(params):
    return (api.get_history_minute_time_data(int(params[0]), params[1], int(params[2])))

def get_transaction_data(params):
    return (api.get_transaction_data(int(params[0]), params[1], int(params[2]), int(params[3])))

def get_history_transaction_data(params):
    return (api.get_history_transaction_data(int(params[0]), params[1], int(params[2]), int(params[3]), int(params[4])))

def get_company_info_category(params):
    return (api.get_company_info_category(int(params[0]), params[1]))

def get_company_info_content(params):
    return (api.get_company_info_content(int(params[0]), params[1].encode("utf-8"), params[2].encode("utf-8"), int(params[3]), int(params[4])))

def get_xdxr_info(params):
    return (api.get_xdxr_info(int(params[0]), params[1]))

def get_finance_info(params):
    return (api.get_finance_info(int(params[0]), params[1]))

FUNCTION_LIST = OrderedDict(
    [
        (1, ['Get stock quotes', 'Param: market code, stock code, e.g.: 0,000001 or 1,600300', get_security_quotes, '0,000001']),
        (2, ['Get K-lines', '''category-> K-line type
0 5min K-line 1 15min K-line 2 30min K-line 3 1hour K-line 4 Daily K-line
5 Weekly K-line
6 Monthly K-line
7 1min
8 1min K-line 9 Daily K-line
10 Quarterly K-line
11 Yearly K-line
market -> Market code 0:Shenzhen, 1:Shanghai
stockcode -> Security code;
start -> Specified range start position;
count -> Number of K-lines to request, max 800

e.g.: 9,0,000001,0,100''', get_security_bars, '9,0,000001,0,100']),
        (3, ['Get market stock count', 'Param: market code, e.g.: 0 or 1', get_security_count, '0']),
        (4, ['Get stock list', 'Param: market code, start position, count, e.g.: 0,0 or 1,100', get_security_list, '0,0']),
        (5, ['Get index K-lines', """Params:
category-> K-line type
0 5min K-line 1 15min K-line 2 30min K-line 3 1hour K-line 4 Daily K-line
5 Weekly K-line
6 Monthly K-line
7 1min
8 1min K-line 9 Daily K-line
10 Quarterly K-line
11 Yearly K-line
market -> Market code 0:Shenzhen, 1:Shanghai
stockCode -> Security code;
start -> Specified range start position; count -> Number of K-lines to request
e.g.: 9,1,000001,0,100""", get_index_bars, '9,1,000001,0,100']),
        (6, ['Query intraday quotes', "Param: market code, stock code, e.g.: 0,000001 or 1,600300", get_minute_time_data, '0,000001']),
        (7, ['Query historical intraday quotes', 'Param: market code, stock code, date, e.g.: 0,000001,20161209 or 1,600300,20161209', get_history_minute_time_data, '0,000001,20161209']),
        (8, ['Query transactions', 'Param: market code, stock code, start position, count, e.g.: 0,000001,0,10', get_transaction_data, '0,000001,0,10']),
        (9, ['Query historical transactions', 'Param: market code, stock code, start position, date, count, e.g.: 0,000001,0,10,20170209', get_history_transaction_data, '0,000001,0,10,20170209']),
        (10, ['Query company info category','Param: market code, stock code, e.g.: 0,000001 or 1,600300', get_company_info_category, '0,000001']),
        (11, ['Read company info detail', 'Param: market code, stock code, filename, start position, count, e.g.: 0,000001,000001.txt,2054363,9221', get_company_info_content, '0,000001,000001.txt,0,10']),
        (12, ['Read ex-rights info', 'Param: market code, stock code, e.g.: 0,000001 or 1,600300', get_xdxr_info, '0,000001']),
        (13, ['Read financial info', 'Param: market code, stock code, e.g.: 0,000001 or 1,600300', get_finance_info, '0,000001']),
    ]
)

#  1 :               CITIC Shenzhen Quotes    119.147.212.81:7709
#  2 :             Huatai Securities (Nanjing Telecom)    221.231.141.60:7709
#  3 :             Huatai Securities (Shanghai Telecom)    101.227.73.20:7709
#  4 :           Huatai Securities (Shanghai Telecom 2)    101.227.77.254:7709
#  5 :        zz

SERVERS = OrderedDict([
(1, ['CITIC Shenzhen Quotes', '119.147.212.81:7709']),
(2, ['Huatai Securities (Nanjing Telecom)', '221.231.141.60:7709']),
(3, ['Huatai Securities (Shanghai Telecom)', '101.227.73.20:7709']),
(4, ['Huatai Securities (Shanghai Telecom 2)', '101.227.77.254:7709']),
(5, ['Huatai Securities (Shenzhen Telecom)', '14.215.128.18:7709']),
(6, ['Huatai Securities (Wuhan Telecom)', '59.173.18.140:7709']),
(7, ['Huatai Securities (Tianjin Unicom)', '60.28.23.80:7709']),
(8, ['Huatai Securities (Shenyang Unicom)', '218.60.29.136:7709']),
(9, ['Huatai Securities (Nanjing Unicom)', '122.192.35.44:7709']),
(10, ['Huatai Securities (Nanjing Unicom)', '122.192.35.44:7709']),
])

def connect():
    while True:
        click.secho("Please select server")
        click.secho("-" * 20)
        for k,v in SERVERS.items():
            click.secho("[%d] :%s (%s)" % (k, v[0], v[1]))
        click.secho("-" * 20)
        num = click.prompt("Please enter number ", type=int, default=1)
        if num not in SERVERS:
            click.echo("Invalid number")
            continue
        ip,port = SERVERS[num][1].split(":")

        c = api.connect(ip, int(port))
        if not c:
            raise Exception("Unable to connect")
        else:
            break

def connect_to(ipandport):
    ip, port = ipandport.split(":")
    c = api.connect(ip, int(port))
    if not c:
        raise Exception("Unable to connect")

def disconnect():
    api.disconnect()

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf8')

FUNCTION_LIST_STR = "0 : Use interactive interface\n"
for x, y in FUNCTION_LIST.items():
    FUNCTION_LIST_STR = FUNCTION_LIST_STR + str(x) + " : " + y[0] + "\n"

@click.command()
@click.option('-f', '--function', default=0, type=click.INT, help="Select function to use" + "\n" + FUNCTION_LIST_STR)
@click.option('--df/--no-df', default=True, help="Whether to use Pandas DataFrame display")
@click.option('-o', '--output', default="-", help="Save to file, default not saved")
@click.option('-s', '--server', default="-", type=click.STRING, help="Server to connect, set to connect directly without selection" )
@click.option('--all/--no-all', default=False, help="Show all server list")
def main(function, df, output, server, all):
    """
    Stock quote program. Author: Alpha
    """

    if all:
        global SERVERS
        SERVERS = OrderedDict([(idx+1, [host[0], "%s:%s" % (host[1], host[2])]) for idx, host in enumerate(hq_hosts)])

    click.secho("Connecting.... ", fg="green")
    if server == '-':
        connect()
    else:
        connect_to(server)

    click.secho("Connected!", fg="green")
    if function == 0:

        while True:
            click.secho("-" * 20)
            click.secho("Function list:")
            for (k,v) in FUNCTION_LIST.items():
                click.secho(str(k) + " : " + v[0], bold=True)
                last = k + 1
            click.secho(str(last) + " : Exit disconnect", bold=True)
            click.secho("-" * 20)
            value = click.prompt('Please enter function to use', type=int)
            if value == last:
                break
            run_function(df, value)
            click.secho("-" * 20)
            click.echo("Press any key to continue")
            click.getchar()
    elif function in FUNCTION_LIST.keys():
        value = function
        result = run_function(df, value)

        if (result is not None) and (output != "-"):
            click.secho("Writing result to " + output)
            if isinstance(result, pd.DataFrame):
                result.to_csv(output)
            else:
                with open(output, "wb") as f:
                    pickle.dump(result, f)

    click.secho("Disconnecting.... ", fg="green")
    disconnect()
    click.secho("Disconnected!", fg="green")


def run_function(df, value):
    click.secho("You selected function " + str(value) + " : " + FUNCTION_LIST[value][0])
    click.secho("-" * 20)
    click.secho(FUNCTION_LIST[value][1])
    params_str = click.prompt("Please enter params ", type=str, default=FUNCTION_LIST[value][3])
    params = [p.strip() for p in params_str.split(",")]
    click.secho("-" * 20)
    try:
        result = FUNCTION_LIST[value][2](params)
        if df:
            result = api.to_df(result)
            click.secho(str(result), bold=True)
            return result
        else:
            pprint.pprint(result)
            return result
    except Exception as e:
        import traceback
        print('-' * 60)
        traceback.print_exc(file=sys.stdout)
        print('-' * 60)
        click.secho("Error occurred, error message: " + str(e), fg='red')


if __name__ == '__main__':
    main()
