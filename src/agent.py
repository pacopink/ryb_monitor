#!/bin/env python
#coding:utf8
import yaml
import socket
import sys
from Entity import *
from CheckTask import AlarmCheckTask, KpiCheckTask
import HttpReporter
from Logger import *
from conf import RygConf

CONF_FILE = "../conf/conf.yml"
log_info("agent starting ...")

myhostname = socket.gethostname()

conf = RygConf(CONF_FILE)
center_host = conf.center_host
center_port = conf.center_port

### ensure singleton ###
lock_port = conf.agent_lock_udp_port
import SocketLock
try:
    SocketLock.acquire()
except Exception,e:
    log_error("agent acquire socket lock on UDP addr [localhost:%d] failed, maybe another agent is running, exit myself.  [%s]", lock_port, e)
    sys.exit(1)

mon_hosts = conf.mon_hosts
states = conf.states
kpis = conf.kpis
threads = conf.threads

#check if my hostname is configured
if  myhostname not in mon_hosts:
    log_error("my hostname [%s] is not configured in config file [%s], exit", myhostname, CONF_FILE)
    sys.exit(1)

#get all my states that need to check
myAlarms = list()
for alarmId in mon_hosts[myhostname]["states"]:
    alarm =  AlarmCheckTask(alarmId, conf.script_path, states[alarmId])
    myAlarms.append(alarm)
    log_info("state: %s", vars(alarm))

myKpis = list()
for kpiId in mon_hosts[myhostname]["kpis"]:
    kpi = KpiCheckTask(kpiId, conf.script_path, kpis[kpiId])
    myKpis.append(kpi)
    log_info("kpi: %s", vars(kpi))

if len(myAlarms) <1 and len(myKpis)<1:
    log_error("there is no alarm[%d] or kpi[%d] checkpoints on [%s], exit", len(myAlarms), len(myKpis), myhostname)
    sys.exit(1)

from multiprocessing import dummy
pool = dummy.Pool(threads)

if __name__=="__main__":

    while True:
        states = filter(lambda x:x is not None, pool.map(lambda x:x.check(), myAlarms))
        #for kpi in myKpis:
        #    print kpi.check()
        kpis = filter(lambda x:x is not None, pool.map(lambda x:x.check(), myKpis))
        if (len(states)>0 or len(kpis)>0):
            msg = AgentReportMsg(myhostname)
            for state in states:
                msg.addstateibute(state)
            for kpi in kpis:
                msg.addKpi(kpi)
            try:
                HttpReporter.report(msg, center_host, center_port)
            except socket.timeout:
                log_error("report failed, connect to indexer timeout, [%s]", msg.toJson())
            except Exception,e:
                log_error("report failed, recev exception: %s, [%s]", e, msg.toJson())
        try:
            time.sleep(1)
        except:
            break


