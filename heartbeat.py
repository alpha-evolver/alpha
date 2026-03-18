# coding=utf-8

from threading import Thread
import random
from alfe.log import DEBUG, log
import time

# Ref: https://stackoverflow.com/questions/6524459/stopping-a-thread-after-a-certain-amount-of-time


DEFAULT_HEARTBEAT_INTERVAL = 10.0  # 10 seconds per heartbeat

class HqHeartBeatThread(Thread):

    def __init__(self, api, stop_event, heartbeat_interval=DEFAULT_HEARTBEAT_INTERVAL):
        self.api = api
        self.client = api.client
        self.stop_event = stop_event
        self.heartbeat_interval = heartbeat_interval
        super(HqHeartBeatThread, self).__init__()

    def run(self):
        while not self.stop_event.is_set():
            self.stop_event.wait(self.heartbeat_interval)
            if self.client and (time.time() - self.api.last_ack_time > self.heartbeat_interval):
                try:
                    # Send a packet to get stock count as heartbeat
                    self.api.do_heartbeat()
                except Exception as e:
                    log.debug(str(e))

