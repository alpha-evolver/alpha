#coding: utf-8
# see https://github.com/alpha-evolver/alfe/issues/38 IP optimization simple method
# by yutianst

import datetime
from alfe.hq import AlfeHq_API
from alfe.exhq import AlfeExHq_API

stock_ip = [{'ip': '106.120.74.86', 'port': 7711, 'name': 'Shanghai Quotes Main 1'},
 {'ip': '113.105.73.88', 'port': 7709, 'name': 'Shenzhen Quotes Main'},
 {'ip': '113.105.73.88', 'port': 7711, 'name': 'Shenzhen Quotes Main'},
 {'ip': '114.80.80.222', 'port': 7711, 'name': 'Shanghai Quotes Main'},
 {'ip': '117.184.140.156', 'port': 7711, 'name': 'Mobile Quotes Main'},
 {'ip': '119.147.171.206', 'port': 443, 'name': 'Guangzhou Quotes Main'},
 {'ip': '119.147.171.206', 'port': 80, 'name': 'Guangzhou Quotes Main'},
 {'ip': '218.108.50.178', 'port': 7711, 'name': 'Hangzhou Quotes Main'},
 {'ip': '221.194.181.176', 'port': 7711, 'name': 'Shanghai Quotes Main 2'},
 {'ip': '106.120.74.86', 'port': 7709},
 {'ip': '112.95.140.74', 'port': 7709},
 {'ip': '112.95.140.92', 'port': 7709},
 {'ip': '112.95.140.93', 'port': 7709},
 {'ip': '113.05.73.88', 'port': 7709},
 {'ip': '114.67.61.70', 'port': 7709},
 {'ip': '114.80.149.19', 'port': 7709},
 {'ip': '114.80.149.22', 'port': 7709},
 {'ip': '114.80.149.84', 'port': 7709},
 {'ip': '114.80.80.222', 'port': 7709},
 {'ip': '115.238.56.198', 'port': 7709},
 {'ip': '115.238.90.165', 'port': 7709},
 {'ip': '117.184.140.156', 'port': 7709},
 {'ip': '119.147.164.60', 'port': 7709},
 {'ip': '119.147.171.206', 'port': 7709},
 {'ip': '119.29.51.30', 'port': 7709},
 {'ip': '121.14.104.70', 'port': 7709},
 {'ip': '121.14.104.72', 'port': 7709},
 {'ip': '121.14.110.194', 'port': 7709},
 {'ip': '121.14.2.7', 'port': 7709},
 {'ip': '123.125.108.23', 'port': 7709},
 {'ip': '123.125.108.24', 'port': 7709},
 {'ip': '124.160.88.183', 'port': 7709},
 {'ip': '180.153.18.17', 'port': 7709},
 {'ip': '180.153.18.170', 'port': 7709},
 {'ip': '180.153.18.171', 'port': 7709},
 {'ip': '180.153.39.51', 'port': 7709},
 {'ip': '218.108.47.69', 'port': 7709},
 {'ip': '218.108.50.178', 'port': 7709},
 {'ip': '218.108.98.244', 'port': 7709},
 {'ip': '218.75.126.9', 'port': 7709},
 {'ip': '218.9.148.108', 'port': 7709},
 {'ip': '221.194.181.176', 'port': 7709},
 {'ip': '59.173.18.69', 'port': 7709},
 {'ip': '60.12.136.250', 'port': 7709},
 {'ip': '60.191.117.167', 'port': 7709},
 {'ip': '60.28.29.69', 'port': 7709},
 {'ip': '61.135.142.73', 'port': 7709},
 {'ip': '61.135.142.88', 'port': 7709},
 {'ip': '61.152.107.168', 'port': 7721},
 {'ip': '61.152.249.56', 'port': 7709},
 {'ip': '61.153.144.179', 'port': 7709},
 {'ip': '61.153.209.138', 'port': 7709},
 {'ip': '61.153.209.139', 'port': 7709},
 {'ip': 'hq.cjis.cn', 'port': 7709},
 {'ip': 'hq1.daton.com.cn', 'port': 7709},
 {'ip': 'jsalfe.gtjas.com', 'port': 7709},
 {'ip': 'shalfe.gtjas.com', 'port': 7709},
 {'ip': 'szalfe.gtjas.com', 'port': 7709},
 {'ip': '113.105.142.162', 'port': 7721},
 {'ip': '23.129.245.199', 'port': 7721}]

future_ip = [{'ip': '106.14.95.149', 'port': 7727, 'name': 'Extended Market Shanghai Dual-line'},
 {'ip': '112.74.214.43', 'port': 7727, 'name': 'Extended Market Shenzhen Dual-line 1'},
 {'ip': '119.147.86.171', 'port': 7727, 'name': 'Extended Market Shenzhen Main'},
 {'ip': '119.97.185.5', 'port': 7727, 'name': 'Extended Market Wuhan Main 1'},
 {'ip': '120.24.0.77', 'port': 7727, 'name': 'Extended Market Shenzhen Dual-line 2'},
 {'ip': '124.74.236.94', 'port': 7721},
 {'ip': '202.103.36.71', 'port': 443, 'name': 'Extended Market Wuhan Main 2'},
 {'ip': '47.92.127.181', 'port': 7727, 'name': 'Extended Market Shanghai Main'},
 {'ip': '59.175.238.38', 'port': 7727, 'name': 'Extended Market Wuhan Main 3'},
 {'ip': '61.152.107.141', 'port': 7727, 'name': 'Extended Market Shanghai Main 1'},
 {'ip': '61.152.107.171', 'port': 7727, 'name': 'Extended Market Shanghai Main 2'},
 {'ip': '119.147.86.171', 'port': 7721, 'name': 'Extended Market Shenzhen Main'},
 {'ip': '47.107.75.159', 'port': 7727, 'name': 'Extended Market Shenzhen Dual-line 3'}]

def ping(ip, port=7709, type_='stock'):
    api = AlfeHq_API()
    apix = AlfeExHq_API()
    __time1 = datetime.datetime.now()
    try:
        if type_ in ['stock']:
            with api.connect(ip, port, time_out=0.7):
                res = api.get_security_list(0, 1)
                #print(len(res))
                if res is not None:
                    if len(res) > 800:
                        print('GOOD RESPONSE {}'.format(ip))
                        return datetime.datetime.now() - __time1
                    else:
                        print('BAD RESPONSE {}'.format(ip))
                        return datetime.timedelta(9, 9, 0)
                else:

                    print('BAD RESPONSE {}'.format(ip))
                    return datetime.timedelta(9, 9, 0)
        elif type_ in ['future']:
            with apix.connect(ip, port, time_out=0.7):
                res = apix.get_instrument_count()
                if res is not None:
                    if res > 20000:
                        print('GOOD RESPONSE {}'.format(ip))
                        return datetime.datetime.now() - __time1
                    else:
                        print('Bad FUTURE IP REPSONSE {}'.format(ip))
                        return datetime.timedelta(9, 9, 0)
                else:
                    print('Bad FUTURE IP REPSONSE {}'.format(ip))
                    return datetime.timedelta(9, 9, 0)
    except Exception as e:
        if isinstance(e, TypeError):
            print(e)
            print('Tushare built-in alfe version and latest alfe version are different, please reinstall alfe to fix this issue')
            print('pip uninstall alfe')
            print('pip install alfe')

        else:
            print('BAD RESPONSE {}'.format(ip))
        return datetime.timedelta(9, 9, 0)



def select_best_ip(_type='stock'):
    """Currently this is single-threaded optimization, if you need multi-process optimization / best ip cache, you can refer to
    https://github.com/QUANTAXIS/QUANTAXIS/blob/master/QUANTAXIS/QAFetch/QAAlfe.py#L106


    Keyword Arguments:
        _type {str} -- [description] (default: {'stock'})
    
    Returns:
        [type] -- [description]
    """
    best_ip = {
        'stock': {
            'ip': None, 'port': None
        },
        'future': {
            'ip': None, 'port': None
        }
    }
    ip_list = stock_ip if _type== 'stock' else future_ip
    
    data = [ping(x['ip'], x['port'], _type) for x in ip_list]
    results = []
    for i in range(len(data)):
        # Remove data that ping failed
        if data[i] < datetime.timedelta(0, 9, 0):
            results.append((data[i], ip_list[i]))
    # Sort by ping value from small to large
    results = [x[1] for x in sorted(results, key=lambda x: x[0])]
    
    return results[0]

if __name__ == '__main__':
    ip = select_best_ip('stock')
    print(ip)
    ip = select_best_ip('future')
    print(ip)
