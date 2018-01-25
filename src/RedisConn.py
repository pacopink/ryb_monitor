#!/bin/env python
#coding:utf8

import redis
def connRedis(redisConf):
    host = redisConf["host"]
    port = redisConf["port"]
    db = redisConf["db"]
    auth=None
    try:
        auth = redisConf["auth"]
    except KeyError:
        pass
    return redis.Redis(host=host, port=port, db=db, password=auth, socket_timeout=5)


def connRedisPool(redisConf, max_connections=4):
    host = redisConf["host"]
    port = redisConf["port"]
    db = redisConf["db"]
    auth=None
    try:
        auth = redisConf["auth"]
    except KeyError:
        pass
    return redis.ConnectionPool(host=host, port=port, db=db, password=auth, max_connections=max_connections, socket_timeout=5)

def getRedisFromPool(connection_pool):
    return redis.Redis(connection_pool=connection_pool)


from multiprocessing import dummy


def slice(keys, segmentLen):
    for i in xrange(0, len(keys), segmentLen):
        yield keys[i:(i+segmentLen)]

class RedisBatch(object):
    def __init__(self, redis_conf, pool_size=2, batch_size=200):
        self.batch_size = batch_size
        self.pool_size = pool_size
        self.tp = dummy.Pool(pool_size)
        self.cp = connRedisPool(redis_conf, pool_size+2) #加上一点冗余连接数

    def redis(self):
        return redis.Redis(connection_pool=self.cp)

    def list_head(self, keys):
        def getByKeys(keys):
            r = getRedisFromPool(self.cp)
            p = r.pipeline()
            for k in keys:
                p.lindex(k, 0)
            vs = p.execute()
            return zip(keys, vs)
        #从redis批量获取结果
        try:
            return reduce(lambda x,y: x+y, self.tp.map(getByKeys, slice(keys, self.batch_size)))
        except:
            return ()

    def hget(self, pk, keys):
        def hgetByKeys(keys):
            r = getRedisFromPool(self.cp)
            p = r.pipeline()
            for k in keys:
                p.hget(pk, k)
            vs = p.execute()
            return zip(keys, vs)
        return reduce(lambda x,y: x+y, self.tp.map(hgetByKeys, slice(keys, self.batch_size)))

    def hgetall(self, key):
        r = getRedisFromPool(self.cp)
        return  r.hgetall(key)

    def ltrim(self, keys, stat_retention, kpi_retention):
        def trimByKeys(keys):
            r = getRedisFromPool(self.cp)
            p = r.pipeline()
            for k in keys:
                if k[0:3] == "KPI":
                    p.ltrim(k, 0, kpi_retention-1)
                else:
                    p.ltrim(k, 0, stat_retention-1)
            p.execute()
        self.tp.map(trimByKeys, slice(keys, self.batch_size))

    def scanByPattern(self, pattern):
        r = getRedisFromPool(self.cp)
        res = list()
        cursor=0
        sr = r.scan(cursor, pattern, self.batch_size)
        cursor = sr[0]
        res += sr[1]
        while cursor!=0:
            sr = r.scan(cursor, pattern, self.batch_size)
            cursor = sr[0]
            res += sr[1]
        return res

    def hscanByPattern(self, key, pattern):
        r = getRedisFromPool(self.cp)
        res = dict()
        cursor=0
        sr = r.hscan(key, cursor, pattern, self.batch_size)
        cursor = sr[0]
        res.update(sr[1])
        while cursor!=0:
            sr = r.scan(cursor, key, pattern, self.batch_size)
            cursor = sr.pop(0)
            res += sr
        return res
