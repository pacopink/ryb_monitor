#!/bin/env python
#coding:utf8

class KeyGen(object):
    '''全局的Redis Key管理器'''
    TS="ts"
    STAT="stat"
    MSG="msg"
    ALARM_SND_ENQUEUE="alarm_snd_enqueue"
    ALARM_SND="alarm_snd"
    #记录历史记录
    STATE_TMP = "STAT:{hostname}:{stateId}"
    KPI_TMP="KPI:{hostname}:{kpiId}"
    ALARM_QUEUE="RYG:ALARM:QUEUE"
    CLEAR_QUEUE="RYG:CLEAR:QUEUE"
    RED_LIGHT="RYG:RED"
    YELLOW_LIGHT="RYG:YELLOW"
    GREEN_LIGHT="RYG:GREEN"

    @staticmethod
    def stateKey(hostname, stateId):
        return KeyGen.STATE_TMP.format(hostname=hostname, stateId=stateId)

    @staticmethod
    def KpiKey(hostname, kpiId):
        return KeyGen.KPI_TMP.format(hostname=hostname, kpiId=kpiId)



