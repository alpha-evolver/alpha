# utf-8
from alfe.log import DEBUG, log
from functools import partial
import time


## Call single API, retry count, if exceeded then no more retry
DEFAULT_API_CALL_MAX_RETRY_TIMES = 20
## Retry interval sleep time
DEFAULT_API_RETRY_INTERVAL = 0.2

class AlfeHqApiCallMaxRetryTimesReachedException(Exception):
    pass

class AlfeHqPool_API(object):
    """
    Implement a connection pool mechanism
    Contains:

    1. One main connection currently communicating data
    2. One backup connection, backup connection also connects to server, maintains connection via heartbeat, when main connection has communication issues, backup connection immediately becomes main connection, original main connection returns to ip pool, and new backup connection is selected from ip pool
    3. m ips constitute ip pool, can get list via some method, list can be sorted, if backup connection is missing, we append to backup connection based on sorting priority
    """

    def __init__(self, hq_cls, ippool):
        self.hq_cls = hq_cls
        self.ippool = ippool
        """
        Client connection currently communicating
        """
        self.api = hq_cls(multithread=True, heartbeat=True)
        """
        Backup connection
        """
        self.hot_failover_api = hq_cls(multithread=True, heartbeat=True)

        self.api_call_max_retry_times = DEFAULT_API_CALL_MAX_RETRY_TIMES
        self.api_call_retry_times = 0
        self.api_retry_interval = DEFAULT_API_RETRY_INTERVAL


        # Reflect on get_* series functions in hq_cls
        log.debug("perform_reflect")
        self.perform_reflect(self.api)

    def perform_reflect(self, api_obj):
        # ref : https://stackoverflow.com/questions/34439/finding-what-methods-an-object-has
        method_names = [attr for attr in dir(api_obj) if callable(getattr(api_obj, attr))]
        for method_name in method_names:
            log.debug("testing attr %s" % method_name)
            if method_name[:3] == 'get' or method_name == "do_heartbeat" or method_name == 'to_df':
                log.debug("set reflection to method: %s", method_name)
                _do_hp_api_call = partial(self.do_hq_api_call, method_name)
                setattr(self, method_name, _do_hp_api_call)

    def do_hq_api_call(self, method_name, *args, **kwargs):
        """
        Proxy send request to actual client
        :param method_name: Method name to call
        :param args: Parameters
        :param kwargs: Key-value parameters
        :return: Call result
        """
        try:
            result = getattr(self.api, method_name)(*args, **kwargs)
            if result is None:
                log.info("api(%s) call return None" % (method_name,))
        except Exception as e:
            log.info("api(%s) call failed, Exception is %s" % (method_name, str(e)))
            result = None

        # If unable to get info, then retry
        if result is None:
            if self.api_call_retry_times >= self.api_call_max_retry_times:
                log.info("(method_name=%s) max retry times(%d) reached" % (method_name, self.api_call_max_retry_times))
                raise AlfeHqApiCallMaxRetryTimesReachedException("(method_name=%s) max retry times reached" % method_name)
            old_api_ip = self.api.ip
            new_api_ip = None
            if self.hot_failover_api:
                new_api_ip = self.hot_failover_api.ip
                log.info("api call from init client (ip=%s) err, perform rotate to (ip =%s)..." %(old_api_ip, new_api_ip))
                self.api.disconnect()
                self.api = self.hot_failover_api
            log.info("retry times is " + str(self.api_call_max_retry_times))
            # Get backup ip from pool again
            new_ips = self.ippool.get_ips()

            choise_ip = None
            for _test_ip in new_ips:
                if _test_ip[0] == old_api_ip or _test_ip[0] == new_api_ip:
                    continue
                choise_ip = _test_ip
                break

            if choise_ip:
                self.hot_failover_api = self.hq_cls(multithread=True, heartbeat=True)
                self.hot_failover_api.connect(*choise_ip)
            else:
                self.hot_failover_api = None
            # Block 0.2 seconds, then recursively call self
            time.sleep(self.api_retry_interval)
            result = self.do_hq_api_call(method_name, *args, **kwargs)
            self.api_call_retry_times += 1

        else:
            self.api_call_retry_times = 0

        return result

    def connect(self, ipandport, hot_failover_ipandport):
        log.debug("setup ip pool")
        self.ippool.setup()
        log.debug("connecting to primary api")
        self.api.connect(*ipandport)
        log.debug("connecting to hot backup api")
        self.hot_failover_api.connect(*hot_failover_ipandport)
        return self

    def disconnect(self):
        log.debug("primary api disconnected")
        self.api.disconnect()
        log.debug("hot backup api  disconnected")
        self.hot_failover_api.disconnect()
        log.debug("ip pool released")
        self.ippool.teardown()

    def close(self):
        """
        Alias for disconnect, to support with closing(obj): syntax
        :return:
        """
        self.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':

    from alfe.hq import AlfeHq_API
    from alfe.pool.ippool import AvailableIPPool
    from alfe.config.hosts import hq_hosts
    import random
    import logging
    import pprint
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    log.addHandler(ch)

    ips = [(v[1], v[2]) for v in hq_hosts]

    # Get 5 random ips as ip pool
    random.shuffle(ips)
    ips5 = ips[:5]

    ippool = AvailableIPPool(AlfeHq_API, ips5)

    primary_ip, hot_backup_ip = ippool.sync_get_top_n(2)

    print("make pool api")
    api = AlfeHqPool_API(AlfeHq_API, ippool)
    print("make pool api done")
    print("send api call to primary ip %s, %s" % (str(primary_ip), str(hot_backup_ip)))
    with api.connect(primary_ip, hot_backup_ip):
        ret = api.get_xdxr_info(0, '000001')
        print("send api call done")
        pprint.pprint(ret)
