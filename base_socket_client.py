# coding=utf-8

#
# Just for practising
#


import os
import socket
import sys
import pandas as pd

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(
        os.path.dirname(os.path.realpath(__file__))))

from alfe.log import DEBUG, log
from alfe.errors import AlfeConnectionError, AlfeFunctionCallError

import threading
import datetime
import time
from alfe.heartbeat import HqHeartBeatThread
import functools
from alfe.parser.raw_parser import RawParser


CONNECT_TIMEOUT = 5.000
RECV_HEADER_LEN = 0x10
DEFAULT_HEARTBEAT_INTERVAL = 10.0


"""
In [7]: 0x7e
Out[7]: 126

In [5]: len(body)
Out[5]: 8066

In [6]: len(body)/126
Out[6]: 64.01587301587301

In [7]: len(body)%126
Out[7]: 2

In [8]: (len(body)-2)/126
Out[8]: 64.0
"""


def update_last_ack_time(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kw):
        self.last_ack_time = time.time()
        log.debug("last ack time update to " + str(self.last_ack_time))
        current_exception = None
        try:
            ret = func(self, *args, **kw)
        except Exception as e:
            current_exception = e
            log.debug("hit exception on req exception is " + str(e))
            if self.auto_retry:
                for time_interval in self.retry_strategy.gen():
                    try:
                        time.sleep(time_interval)
                        self.disconnect()
                        self.connect(self.ip, self.port)
                        ret = func(self, *args, **kw)
                        if ret:
                            return ret
                    except Exception as retry_e:
                        current_exception = retry_e
                        log.debug(
                            "hit exception on *retry* req exception is " + str(retry_e))

                log.debug("perform auto retry on req ")

            self.last_transaction_failed = True
            ret = None
            if self.raise_exception:
                to_raise = AlfeFunctionCallError("calling function error")
                to_raise.original_exception = current_exception if current_exception else None
                raise to_raise
        """
        If raise_exception=True, raise exception
        If raise_exception=False, return None
        """
        return ret
    return wrapper


class RetryStrategy(object):
    @classmethod
    def gen(cls):
        raise NotImplementedError("need to override")


class DefaultRetryStrategy(RetryStrategy):
    """
    Default retry strategy. You can write your own retry strategy to replace this one.
    The strategy mainly implements the gen method, which is a generator that returns
    the interval time for the next retry in seconds. We will use time.sleep to wait
    synchronously here before reconnecting, then retry the original request until gen ends.
    """
    @classmethod
    def gen(cls):
        # Default retry 4 times... time intervals as below
        for time_interval in [0.1, 0.5, 1, 2]:
            yield time_interval


class TrafficStatSocket(socket.socket):
    """
    Socket class with traffic statistics support
    """

    def __init__(self, sock, mode):
        super(TrafficStatSocket, self).__init__(sock, mode)
        # Traffic statistics related
        self.send_pkg_num = 0  # Number of sends
        self.recv_pkg_num = 0  # Number of receives
        self.send_pkg_bytes = 0  # Bytes sent
        self.recv_pkg_bytes = 0  # Bytes received
        self.first_pkg_send_time = None  # First packet send time

        self.last_api_send_bytes = 0  # Send bytes of last API call
        self.last_api_recv_bytes = 0  # Receive bytes of last API call


class BaseSocketClient(object):

    def __init__(self, multithread=False, heartbeat=False, auto_retry=False, raise_exception=False):
        self.need_setup = True
        if multithread or heartbeat:
            self.lock = threading.Lock()
        else:
            self.lock = None

        self.client = None
        self.heartbeat = heartbeat
        self.heartbeat_thread = None
        self.stop_event = None
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL  # Default 10 seconds per heartbeat
        self.last_ack_time = time.time()
        self.last_transaction_failed = False
        self.ip = None
        self.port = None

        # Whether to retry
        self.auto_retry = auto_retry
        # Can override this property to use new retry strategy
        self.retry_strategy = DefaultRetryStrategy()
        # Whether to raise exception on function call error
        self.raise_exception = raise_exception

    def connect(self, ip='101.227.73.20', port=7709, time_out=CONNECT_TIMEOUT, bindport=None, bindip='0.0.0.0'):
        """

        :param ip:  Server IP address
        :param port:  Server port
        :param time_out: Connection timeout
        :param bindport: Local port to bind
        :param bindip: Local IP to bind
        :return: Whether connection is successful True/False
        """

        self.client = TrafficStatSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(time_out)
        log.debug("connecting to server : %s on port :%d" % (ip, port))
        try:
            self.ip = ip
            self.port = port
            if bindport is not None:
                self.client.bind((bindip, bindport))
            self.client.connect((ip, port))
        except socket.timeout as e:
            # print(str(e))
            log.debug("connection expired")
            if self.raise_exception:
                raise AlfeConnectionError("connection timeout error")
            return False
        except Exception as e:
            if self.raise_exception:
                raise AlfeConnectionError("other errors")
            return False

        log.debug("connected!")

        if self.need_setup:
            self.setup()

        if self.heartbeat:
            self.stop_event = threading.Event()
            self.heartbeat_thread = HqHeartBeatThread(
                self, self.stop_event, self.heartbeat_interval)
            self.heartbeat_thread.start()
        return self

    def disconnect(self):

        if self.heartbeat_thread and \
                self.heartbeat_thread.is_alive():
            self.stop_event.set()

        if self.client:
            log.debug("disconnecting")
            try:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
                self.client = None
            except Exception as e:
                log.debug(str(e))
                if self.raise_exception:
                    raise AlfeConnectionError("disconnect err")
            log.debug("disconnected")

    def close(self):
        """
        Alias for disconnect, to support with closing(obj): syntax
        :return:
        """
        self.disconnect()

    def get_traffic_stats(self):
        """
        Get traffic statistics info
        :return:
        """
        if self.client.first_pkg_send_time is not None:
            total_seconds = (datetime.datetime.now() -
                             self.client.first_pkg_send_time).total_seconds()
            if total_seconds != 0:
                send_bytes_per_second = self.client.send_pkg_bytes // total_seconds
                recv_bytes_per_second = self.client.recv_pkg_bytes // total_seconds
            else:
                send_bytes_per_second = None
                recv_bytes_per_second = None
        else:
            total_seconds = None
            send_bytes_per_second = None
            recv_bytes_per_second = None

        return {
            "send_pkg_num": self.client.send_pkg_num,
            "recv_pkg_num": self.client.recv_pkg_num,
            "send_pkg_bytes": self.client.send_pkg_bytes,
            "recv_pkg_bytes": self.client.recv_pkg_bytes,
            "first_pkg_send_time": self.client.first_pkg_send_time,
            "total_seconds": total_seconds,
            "send_bytes_per_second": send_bytes_per_second,
            "recv_bytes_per_second": recv_bytes_per_second,
            "last_api_send_bytes": self.client.last_api_send_bytes,
            "last_api_recv_bytes": self.client.last_api_recv_bytes,
        }

    # for debuging and testing protocol
    def send_raw_pkg(self, pkg):
        cmd = RawParser(self.client, lock=self.lock)
        cmd.setParams(pkg)
        return cmd.call_api()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def to_df(self, v):
        if isinstance(v, list):
            return pd.DataFrame(data=v)
        elif isinstance(v, dict):
            return pd.DataFrame(data=[v, ])
        else:
            return pd.DataFrame(data=[{'value': v}])
