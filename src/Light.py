#!/bin/evn python
#coding: utf8
import time
from Entity import EntityException
from Entity import KpiRecord, StateRecord
from Logger import *


class Light(object):
    '''一个告警灯'''
    def __init__(self):
        self.createTs = 0
        self.lastTs = 0
        self.alarmTs = 0
        self.obj = None
        self.name = None
        self.desc = None
        self.msg = None
        self.alarmInterval = 3600
        self.needClear = False

    def __str__(self):
        needClear = 0
        if self.needClear:
            needClear = 1
        return "%d|%d|%d|%s|%s|%s|%s|%d|%d"%(self.createTs, self.lastTs, self.alarmTs, self.obj, self.name, self.desc, self.msg, self.alarmInterval, needClear)

    def __repr__(self):
        return self.__str__()

    def dumps(self):
        return self.__str__()

    @staticmethod
    def loads(str):
        l = str.split('|')
        if (len(l)!=9):
            raise EntityException("Light.fromString error")
        light = Light()
        light.createTs = int(l[0])
        light.lastTs = int(l[1])
        light.alarmTs = int(l[2])
        light.obj = l[3]
        light.name = l[4]
        light.desc = l[5]
        light.msg = l[6]
        light.alarmInterval = int(l[7])
        needClear = int(l[8])
        if needClear!=0:
            light.needClear = True
        else:
            light.needClear = False
        return light


class LightChecker(object):
    '''根据状态，分类产生信号灯'''
    def __init__(self, conf):
        self.conf = conf

    def check(self, snapshoot):
        self.red = list()
        self.yellow = list()
        self.green = list()

        now = int(time.time())
        for s in snapshoot:
            try:
                key = s[0]
                val = s[1]
                typ, hn, id = key.split(':')
                log_debug("key:%s, type:%s, hn:%s, id:%s val:%s", key, typ, hn, id, val)
                if typ == "KPI":
                    kpiRecord = None
                    if val is not None:
                        kpiRecord = KpiRecord.loads(val)
                    kpi = self.conf.kpis[id]
                    self.checkKpi(now, key, kpi, kpiRecord)
                elif typ == "STAT":
                    statRecord = None
                    if val is not None:
                        statRecord = StateRecord.loads(val)
                    stat = self.conf.states[id]
                    self.checkState(now, key, stat, statRecord)
                else:
                    pass
            except KeyError,e:
                log_warn("LightChecker.check KeyError key:%s, val:%s, errmsg:%s", key, val, e)

    def checkState(self, ts, key, stat, statRecord):
        light = Light()
        light.obj = key
        light.createTs = ts
        light.lastTs = ts
        light.alarmTs = 0
        light.name = stat.name
        light.needClear = stat.needClear
        if statRecord is None:
            light.msg="no stat reported yet, please check"
            self.yellow.append(light)
        else:
            if statRecord.stat != 0:  #状态非0的，挂红灯
                light.msg = key+" "+stat.alarmMsg
                light.desc = statRecord.msg
                self.red.append(light)
            elif (ts-statRecord.ts)>stat.interval*3: #连续3个周期没有更新的，红灯
                light.msg = key+" "+"状态连续3个周期未更新，请检查"
                light.desc = "状态连续3个周期未更新"
                self.red.append(light)
            else:
                self.green.append(light)

    def checkKpi(self, ts, key, kpi, kpiRecord):
        light = Light()
        light.obj = key
        light.createTs = ts
        light.lastTs = ts
        light.alarmTs = 0
        light.name = kpi.name
        light.needClear = kpi.needClear
        if kpiRecord is None:
            light.msg="no kpi reported yet, please check"
            self.yellow.append(light)
        else:
            if kpi.min is not None and kpi.min>kpiRecord.value:
                light.msg = key+","+kpi.name+","+"%d低于下限%d"%(kpiRecord.value, kpi.min)
                light.desc = light.msg
                self.red.append(light)
            elif kpi.max is not None and kpi.max<kpiRecord.value:
                log_debug("%s  %d", kpiRecord, kpi.max)
                light.msg = key+","+kpi.name+","+u"%d超过上限%d"%(kpiRecord.value, kpi.max)
                light.desc = light.msg
                self.red.append(light)
            elif (ts-kpiRecord.ts)>kpi.interval*3:
                light.msg = key+" "+"状态连续3个周期未更新，请检查"
                light.desc = "状态连续3个周期未更新"
                self.red.append(light)
            else:
                self.green.append(light)

def lightsFromDict(d):
    r = dict()
    for k,v in d.items():
        #log_debug(k)
        #log_debug(v)
        light = Light.loads(v)
        r[k] = light
    return r

if __name__=="__main__":
    light = Light()
    light.msg = "abdedfdfd"+" "+"状态连续3个周期未更新，请检查"
    light.desc = "状态连续3个周期未更新"
    #print light.__str__()
    #print vars(light)
    print light
