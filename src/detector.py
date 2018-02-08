#!/bin/env python
#coding: utf-8
'''scan all states and kpis and detect for alarms'''
from multiprocessing import dummy

from KeyGen import KeyGen
from RedisConn import *
from conf import *
from Light import *

REDIS_BATCH=100
MAX_THREADS=10
CHECK_INTERVAL=10 #10s 扫描一次所有状态,改变灯状态
cfgFile = "../conf/conf.yml"

if __name__=="__main__":
    log_info("detector start ...")
    conf = RygConf(cfgFile)

    log_debug("init pools")
    rb = RedisBatch(conf.redis_conf, pool_size=MAX_THREADS, batch_size=REDIS_BATCH)

    #获取所有需要检查的state和list的key

    checkpoints = list()
    for hn, v in conf.mon_hosts.items():
        if 'states' in v:
            checkpoints += map(lambda x: KeyGen.stateKey(hn,x), v['states'])
        if 'kpis' in v:
            checkpoints += map(lambda x: KeyGen.KpiKey(hn,x), v['kpis'])

    log_debug("get all keys ok")


    lc = LightChecker(conf)

    lastHousekeepTs=0
    HOUSEKEEP_INTERVAL=900 #15min一次
    while True:
        now = int(time.time())
        if now-lastHousekeepTs>HOUSEKEEP_INTERVAL:
            log_info("do housekeep to trim states and kpis lists")
            lastHousekeepTs=now
            try:
                rb.ltrim(checkpoints, conf.state_retention, conf.kpi_retention)
            except Exception,e:
                log_error("housekeep encounter error: %s", e)

        log_info("begin checking")
        #从redis批量获取结果
        snapshoot = rb.list_head(checkpoints)
        log_info("get states and kpis snapshoot")
        #print snapshoot

        log_info("new lights collecting ...")
        lc.check(snapshoot)

        #获取当前所有灯信号
        log_info("get current lights")
        current_yellow = lightsFromDict(rb.hgetall(KeyGen.YELLOW_LIGHT))
        current_red = lightsFromDict(rb.hgetall(KeyGen.RED_LIGHT))

        r = rb.redis()
        #处理红灯
        for red in lc.red:
            log_info("RED LIGHT!!! [%s]", red.dumps())
            p = r.pipeline()
            trapFlag = True
            if red.obj in current_red:
                current = current_red[red.obj]
                red.createTs = current.createTs
                red.alarmTs = current.alarmTs
                #如果当前红灯产生时间在之前红灯告警之间的alarmInterval之后，需要新产生一条告警
                if red.lastTs-red.alarmTs<red.alarmInterval:
                    trapFlag = False
            elif red.obj in current_yellow:
                trapFlag = True
                p.hdel(KeyGen.YELLOW_LIGHT, red.obj)

            if trapFlag:
                red.alarmTs = red.lastTs
                p.lpush(KeyGen.ALARM_QUEUE, red.dumps())
                log_info("TRAP ALARM: [%s]", red.dumps())
            p.hset(KeyGen.RED_LIGHT, red.obj, red.dumps())
            p.execute()

        #处理黄灯
        for yellow in lc.yellow:
            log_info("YELLOW LIGHT!!! [%s]", yellow.dumps())
            if yellow.obj in current_red:
                continue
            elif yellow.obj in current_yellow:
                current = current_yellow[yellow.obj]
                yellow.createTs=current.createTs
            r.hset(KeyGen.YELLOW_LIGHT, yellow.obj, yellow.dumps())

        #处理绿灯
        for green in lc.green:
            if green.obj in current_red: #如果原先是红灯
                current = current_red[green.obj]
                if current.alarmTs>0 and current.needClear:
                    #如果发过告警并且需要清理的告警，触发一条清理告警
                    current.msg = '[恢复]'+current.msg
                    log_info("TRAP CLEAR: [%s]", current.dumps())
                    r.lpush(KeyGen.ALARM_QUEUE, current.dumps())
                #摘除红灯
                r.hdel(KeyGen.RED_LIGHT, green.obj)
            elif green.obj in current_yellow:
                #摘除黄灯
                r.hdel(KeyGen.YELLOW_LIGHT, green.obj)

        try:
            time.sleep(CHECK_INTERVAL) #睡interval
        except:
            break



    log_info("detector exit")
