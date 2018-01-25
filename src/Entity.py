#!/bin/env python
#coding: utf-8
import json
import time

from Logger import *

class EntityException(Exception):
    pass


#### 以下三个是网络传输的JSON对应结构体 ####
class State(dict):
    def __init__(self, id, stat, msg):
        self["id"] = id
        self["stat"] = stat
        self["msg"] = msg

    @staticmethod
    def fromDict(d):
        return State(d["id"], d["stat"], d["msg"])

class KPI(dict):
    def __init__(self, id, value):
        self["id"] = id
        self["value"] = value
    @staticmethod
    def fromDict(d):
        return KPI(d["id"],  d["value"])

class AgentReportMsg(dict):
    def __init__(self, hostname):
        self["hostname"] = hostname
        self["ts"] = int(time.time())
        self["state"] = list()
        self["kpi"] = list()

    def addstateibute(self, state):
        self["state"].append(state)

    def addKpi(self, kpi):
        self["kpi"].append(kpi)

    def toJson(self):
        s = json.dumps(self, ensure_ascii=False, indent=2, allow_nan=True, encoding='UTF-8')
        return s

    @staticmethod
    def fromJson(jsonstring):
        data = json.loads(jsonstring, encoding='UTF-8')
        msg = AgentReportMsg(data["hostname"])
        for state in data["state"]:
            msg["state"].append(State.fromDict(state))
        for kpi in data["kpi"]:
            msg["kpi"].append(KPI.fromDict(kpi))
        return msg

#### 以下是Redis存储的信息和对象的映射 #####

class StateRecord(object):
    '''一个状态记录'''
    def __init__(self):
        self.ts = 0
        self.stat = 0
        self.msg = None

    def __str__(self):
        return "%d|%d|%s"%(self.ts, self.stat, self.msg)

    def dumps(self):
        return self.__str__()

    @staticmethod
    def loads(str):
        log_debug(str)
        l = str.split('|')
        if (len(l)!=3):
            raise EntityException("stateRecord.loads err")
        ar = StateRecord()
        ar.ts = int(l[0])
        ar.stat = int(l[1])
        ar.msg = l[2]
        return ar

    @staticmethod
    def loadstateibute(ts, state):
        ar = StateRecord()
        ar.ts = ts
        ar.stat = state["stat"]
        ar.msg = state["msg"]
        return ar

class KpiRecord(object):
    '''一个KPI记录'''
    def __init__(self):
        self.ts = 0
        self.value = 0

    def __str__(self):
        return "%d|%d"%(self.ts, self.value)

    def dumps(self):
        return self.__str__()

    @staticmethod
    def loads(str):
        log_debug(str)
        l = str.split('|')
        if (len(l)!=2):
            raise EntityException("KpiRecord.loads err")
        kpi = KpiRecord()
        kpi.ts = int(l[0])
        kpi.value = int(l[1])
        return kpi

    @staticmethod
    def loadstateibute(ts, kpi):
        k = KpiRecord()
        k.ts = ts
        k.value = kpi["stat"]
        return k



if __name__=="__main__":
    msg = AgentReportMsg("localhost")
    msg.addstateibute(State(1, 0, '我爱北京天安门'))
    msg.addstateibute(State(2, 1, "desc1"))
    msg.addstateibute(State(3, 0, None))
    msg.addKpi(KPI(1,  800))
    msg.addKpi(KPI(2,  800))
    #print repr(msg)
    #import json
    #s = json.dumps(msg, ensure_ascii=False, indent=2, allow_nan=True, encoding='UTF-8')
    #s = json.dumps(msg, cls=MsgEncoder, ensure_ascii=False, indent=2, allow_nan=True, encoding='UTF-8')
    s = msg.toJson()
    print s
    ss = AgentReportMsg.fromJson(s)
    print ss.toJson()



