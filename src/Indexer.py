#!/bin/env python
#coding: utf8

import Queue
import threading
import time
import redis
from RedisConn import connRedis

from KeyGen import KeyGen
from conf import RygConf
from Logger import *

class Indexer(threading.Thread):
    '''对来自Agent的报告，索引到存储中间件'''
    def __init__(self, queue, conf):
        threading.Thread.__init__(self)
        self.conf = conf
        self.redis = connRedis(conf.redis_conf)
        self.q = queue

    def run(self):
        log_info("Processor thread %s start", self.getName())
        self.runFlag = True
        idleCount = 0
        while self.runFlag:
            try:
                msg = self.q.get_nowait()
                self.processRecord(msg)
                idleCount = 0
            except Queue.Empty:
                idleCount+=1
                if idleCount%60 ==0:
                    self.redis.ping() #心跳保活
                if idleCount%600 == 0:
                    log_info("queue empty %s", self.getName())
                time.sleep(0.5)
        log_info("Processor thread %s end", self.getName())

    def terminate(self):
        self.runFlag = False

    def processRecord(self, record):
        log_debug("Processor [%s] [%s]", self.getName(), record)
        self.hn = record["hostname"]
        self.ts = record["ts"]
        pipe = self.redis.pipeline() #使用pipe批量更新到redis，减少IO
        for state in record["state"]:
            self.processstateibute(state, pipe)
        for kpi in record["kpi"]:
            self.processKpi(kpi, pipe)
        pipe.execute()

    def processstateibute(self, state, pipe):
        '''simply update to redis'''
        id = state["id"]
        stat = state["stat"]
        msg = state["msg"]
        if id not in self.conf.states:
            log_warn("unrecognized stateibute, discard it: %s:%d:%s", id, stat, msg)
            return
        val = "%d|%d|%s"%(self.ts, stat, msg[0:256])
        key = KeyGen.stateKey(self.hn, id)
        pipe.lpush(key, val)

    def processKpi(self, kpi, pipe):
        id = kpi["id"]
        value = kpi["value"]
        if id not in self.conf.kpis:
            log_warn("unrecognized kpi, discard it: %s:%d", id, value)
            return
        key = KeyGen.KpiKey(self.hn, id)
        val = "%s|%d"%(self.ts, value)
        pipe.lpush(key, val)


if __name__=="__main__":
    cfgFile="../conf/conf.yml"
    conf = RygConf.load(cfgFile)
    r = connRedis(conf.redis_conf)
    print r.ping()
