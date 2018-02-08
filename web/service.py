#!/bin/env python
#coding: utf8

from conf import *
from RedisConn import *
from KeyGen import KeyGen
from Light import *
import json

CONF_FILE="../conf/conf.yml"

conf = RygConf(CONF_FILE)
rb = RedisBatch(conf.redis_conf, pool_size=8)

def getHosts():
    h = conf.mon_hosts.keys()
    h.sort()
    return h

def getObjNameByObjId(objId):
    typ, hostname, id = objId.split(':')
    name = 'NaN'
    if typ == 'KPI':
        k = conf.kpis.get(id, None)
        if k is not None:
            name = k.name.decode('UTF-8')
    else:
        k = conf.states.get(id, None)
        if k is not None:
            name = k.name.decode('UTF-8')
    return name


def deserializeRecord(x):
    '''记录字符串转换为对象'''
    objId = x[0]
    str = x[1]
    try:
        typ, hostname, id = objId.split(':')
        rec = None
        if typ == "KPI":
            rec = KpiRecord.loads(str)
        else:
            rec = StateRecord.loads(str)
        return vars(rec)
    except:
        return None


def getLights(hostname='all'):
    '''获取所有灯信号'''
    res = dict()
    r = rb.redis()
    pattern = "*"
    if hostname!='all':
        pattern = "*:"+hostname+":*"
    #res['red'] = rb.hscanByPattern(KeyGen.RED_LIGHT, pattern)
    #res['yellow'] = rb.hscanByPattern(KeyGen.YELLOW_LIGHT, pattern)
    res['red'] = dict(map(lambda x: (x[0], vars(Light.loads(x[1]))),  rb.hscanByPattern(KeyGen.RED_LIGHT, pattern).items()))
    res['yellow'] = dict(map(lambda x: (x[0], vars(Light.loads(x[1]))),  rb.hscanByPattern(KeyGen.YELLOW_LIGHT, pattern).items()))
    return res

def getObjListByHostName(isKpi=False, hostname='all'):
    '''按类型和hostname获取最新状态'''
    pattern = "STAT:"
    if isKpi:
        pattern = "KPI:"
    if hostname!='all':
        pattern+=hostname+":"
    pattern+="*"

    objIds = rb.scanByPattern(pattern)
    objIds.sort()
    names = map(getObjNameByObjId, objIds)
    datas = filter(lambda x:x is not None, map(deserializeRecord, rb.list_head(objIds)))
    return map (lambda x: {"id":x[0], "name":x[1], "data":x[2]}, zip(objIds, names, datas))

def getObjHistory(objId, count=1000):
    r = rb.redis()
    name = getObjNameByObjId(objId)
    l = filter(lambda x:x is not None, map(lambda x:deserializeRecord((objId, x)), r.lrange(objId, 0, count-1)))
    return {'id':objId, 'name':name, 'dataList':l}

def getSummary(hn='all', detail=False):
    '''当simple标识有效,只返回红黄灯和主机列表,不返回detail'''
    res=dict()
    if hn != 'all':
        if hn in getHosts():
            res['lights'] = getLights(hn)
            res['states'] = getObjListByHostName(isKpi=False, hostname=hn)
            res['kpis'] = getObjListByHostName(isKpi=True, hostname=hn)
            return res
        else:
            return None
    else:
        res['lights'] = getLights()
        res['hosts'] = getHosts()
        if detail:
            res['details'] = dict()
            for hn in res['hosts']:
                res['details'][hn] = getSummary(hn)
        return res

if __name__=="__main__":
    x=getSummary()
    print x
    print json.dumps(x, indent=4, ensure_ascii=False, encoding='UTF-8')


    x = getSummary('hp')
    print json.dumps(x, indent=4, ensure_ascii=False, encoding='UTF-8')







