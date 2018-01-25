#!/bin/env python
#coding: utf8

from conf import *
from Logger import *
from RedisConn import *
from KeyGen import KeyGen
from Light import Light
import time
import SmsSend

BATCH=20
POLL_INTERVAL=5

log_info("notifier started")
CONF_FILE="../conf/conf.yml"
RECV_FILE="../conf/recv.yml"
conf = RygConf(CONF_FILE)
recv_conf = RecvConf(RECV_FILE)
log_info("config loaded")
pool = connRedisPool(conf.redis_conf)
log_info("redis connected, enter polling loop")
while True:
    r = getRedisFromPool(pool)
    p = r.pipeline()
    for i in xrange(0, BATCH):
        p.rpop(KeyGen.ALARM_QUEUE)
    alarms = p.execute()
    for alarm in alarms:
        if alarm is not None:
            log_info("get alarm line [%s]", alarm)
            try:
                l = Light.loads(alarm)
                id = l.obj.split(":")[2]
                recvs = recv_conf.getRecieverSet(id)
                if len(recvs) == 0:
                    log_warn("cannot find receiver list for [%s] [%s]", id, l.msg)
                for recv in recvs:
                    log_info("TO[%s] [%s]", recv, l.msg)
                    try:
                        SmsSend.send_msg(recv_conf.sms_url, recv, l.msg)
                    except Exception, e:
                        log_error("send sms encounter error [%s]", e)
            except Exception, e:
                log_error("processing alarm line[%s] encounter error[%s]", alarm, e)

    try:
        time.sleep(POLL_INTERVAL)
    except:
        break
log_info("notifier exited")
