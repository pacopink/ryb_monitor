#!/bin/env python
#coding:utf8
import yaml

from yaml import Loader, SafeLoader

class RygConfException(Exception):
    pass

class RygConf(object):
    def __init__(self, path):
        self.path = path
        self.reload()

    def reload(self):
        conf = yaml.load(open(self.path, 'r'))
	self.agent_lock_udp_port = conf['agent_lock_udp_port']
        self.conf = conf
        self.center_host = conf['center_host']
        self.center_port = conf['center_port']
        self.threads = conf["threads"]
        self.mon_hosts = conf['hosts']
        self.redis_conf = conf['redis']
        self.state_retention = conf['state_retention']
        self.kpi_retention = conf['kpi_retention']
        self.script_path = conf['script_path']

        self.states = dict()
        for (k, v) in conf['states'].items():
            self.states[k] = RygStat(v)

        self.kpis = dict()
        for (k, v) in conf['kpis'].items():
            self.kpis[k] = RygKpi(v)

    @staticmethod
    def load(path):
        return RygConf(path)


class GenericCheckPoint(object):
    def __init__(self,  d):
        self.name = d["name"].encode('utf-8')
        self.interval = d["interval"]
        self.probe = d["probe"]
        self.needClear = False
        if 'needClear' in d and d["needClear"]:
            self.needClear = True
        #if 'needClear' in d and d['needClear'] in ['true', "True", "TRUE", 1]:
        #    self.needClear = True
    def __str__(self):
        klass = self.__class__.__name__
        return "%s:%s"%(klass, vars(self))

class RygStat(GenericCheckPoint):
    def __init__(self,  d):
        GenericCheckPoint.__init__(self, d)
        self.alarmMsg = d["alarmMsg"].encode('utf-8')
        self.alarmInterval = d["alarmInterval"]

class  RygKpi(GenericCheckPoint):
    def __init__(self, d):
        GenericCheckPoint.__init__(self, d)
        self.max = None
        self.min = None
        self.alarmMsg = None
        self.alarmInterval = None
        if 'alarmMsg' in d:
            self.alarmMsg = d["alarmMsg"].encode('utf-8')
        if 'alarmInterval' in d:
            self.alarmInterval = d["alarmInterval"]
        try:
            self.max = int(d["max"])
            self.min = int(d["min"])
        except Exception,e:
            pass


class RecvConf:
    def __init__(self, path):
        self.path = path
        self.reload()
        self.cachedRecvSet = dict()

    def reload(self):
        self.conf = yaml.load(open(self.path, 'r'))
        self.sms_url = self.conf["sms_url"]
        self.groups = dict()

        for groupName, numbers in self.conf["groups"].items():
            numSet = set(numbers)
            self.groups[groupName] = numSet

        self.alarmMap = dict()
        for prefix, groupNames in self.conf["alarmMap"].items():
            numbers = reduce(lambda x,y: x.union(y),
                             filter(lambda x:x is not None,
                                            map(lambda x: self.groups.get(x, None), groupNames)))
            if len(numbers)<1:
                raise  RygConfException("empty recv number list found for alarmMap [%s] found, check file [%s]"%(prefix, self.path))
            self.alarmMap[prefix] = numbers


    def getRecieverSet(self, id):
        if id in self.cachedRecvSet:
            return self.cachedRecvSet[id]

        def filterFunc(x):
            key = x[0]
            if (key=="*" or id.find(key)==0):
                return True
            else:
                return False
        #找出所有前缀匹配的用户组
        groups2snd = map(lambda x: x[0], filter(filterFunc, self.alarmMap.items()))
        #把各个集合最终做一个并集
        result = reduce(lambda x,y: x.union(y), map(lambda gn: self.alarmMap[gn], groups2snd))
        self.cachedRecvSet[id] = result
        return result

    def __repr__(self):
        s = ""
        s += self.conf.__repr__()
        s += "\n"
        s += self.sms_url
        s += "\n"
        s += self.groups.__repr__()
        s += "\n"
        s += self.alarmMap.__repr__()
        return s

if __name__=="__main__":
    from Logger import *
    setLevel(DEBUG)
    confFile="../conf/conf.yml"
    conf = RygConf(confFile)
    print conf
    log_debug("llll %s %s", "dfj", "paco")
    recvFile = "../conf/recv.yml"
    recv_conf = RecvConf(recvFile)
    print recv_conf
    print recv_conf.getRecieverSet("a0.0001")
    print recv_conf.getRecieverSet("a0.0002")
    print recv_conf.getRecieverSet("a0.0003")
    print recv_conf.getRecieverSet("a0.0001")
    print recv_conf.getRecieverSet("k0.0001")
    print recv_conf.getRecieverSet("k0.0001")
