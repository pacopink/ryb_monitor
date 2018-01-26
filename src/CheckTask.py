#!/bin/env python
#coding:utf8

import os
import threading
import time
from Logger import *

from Entity import State, KPI

ERR_EXECUTE=-999

def exec_cmd(command, timeout):
    """call shell-command and either return its output or kill it 
    if it doesn't normally exit within timeout seconds and return None"""
    import subprocess, datetime, os, time, signal
    cmd = command.split(" ")
    start = datetime.datetime.now()
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ###避免buffer满堵塞pipe，这里使用一个独立的线程来接收标准输出和标准出错###
        output = [None, None]
        def gatherOutput():
            output[0] = process.stdout.read()
            output[1] = process.stderr.read()
        t = threading.Thread(target=gatherOutput)
        t.start()

        while process.poll() is None:
            time.sleep(0.1)
            now = datetime.datetime.now()
            if (now - start).seconds > timeout:
                os.kill(process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                t.join(0.1)
                return (2, "TIMEOUT", "TIMEOUT")
        t.join(2) #wait for output collection
        return (process.returncode, output[0], output[1])
    except Exception,e :
        return (ERR_EXECUTE, e.__str__(), e.__str__())

class CheckTaskException(Exception):
    '''used to raise exception for CheckTask'''
    pass

class CheckTask(object):
    '''检查任务基类'''
    def __init__(self, id, script_path, checkPointMap):
        self.id = id
        self.last = 0
        self.interval=checkPointMap.interval
        self.timeout=5 #默认执行probe超时为5s
        self.name=checkPointMap.name

        self.probe = os.path.join(script_path, checkPointMap.probe)
        script = self.probe.split(" ")[0]
        if not os.path.isfile(script):
            raise CheckTaskException("probe file %s not exist" % self.probe)

    def needWakeUp(self):
        now = int(time.time())
        if (now - self.last)<self.interval:
            return False
        else:
            self.last = now
            return True

    def check(self):
        '''检查是否到了interval，如果是调用doCheck做实际的探测'''
        if not self.needWakeUp():
            return None
        return self.doCheck()

    def doCheck(self):
        '''重载此函数，定义检测任务的行为'''
        pass

class KpiCheckTask(CheckTask):
    def __init__(self, id, script_path, map):
        CheckTask.__init__(self, id, script_path, map)

    def doCheck(self):
        (stat, stdout, stderr) = exec_cmd(self.probe, self.timeout)
        if stat!=0:
            log_error("check:[%s] [%s] failed with stat[%d] stdout[%s] stderr[%s]", self.id, self.probe, stat, stdout, stderr)
            return None
        val = -999
        try:
            val = int(stdout)
        except  Exception, e:
            log_error("check:[%s] [%s] failed to get kpi value with stat[%d] stdout[%s] stderr[%s]", self.id, self.probe, stat, stdout, stderr)
            return None
        kpi = KPI(self.id, val)
        log_info("check result [%s]", kpi)
        return kpi

class AlarmCheckTask(CheckTask):
    '''每个告警检查项，执行一个脚本获取返回值和大屏信息'''
    def __init__(self, id, script_path, map):
        CheckTask.__init__(self, id,  script_path, map)

    def doCheck(self):
        (stat, msg, stderr) = exec_cmd(self.probe, self.timeout)
        if stat != 0:
            log_error("check[%s] [%s] failed  with stat[%d] stdout[%s] stderr[%s]", self.id, self.probe, stat, msg, stderr)
        state = State(self.id, stat, msg.strip())
        log_info("check result [%s]", state)
        return state

if __name__=="__main__":
    print exec_cmd("../scripts/ps.sh", 3)
    print exec_cmd("ps -ef|wc -l", 3)
    print exec_cmd("../scripts/http_hb.py http://221.180.247.78/lbs_web/probe/streaming.txt", 3)
    #print exec_cmd("tree /home/paco/", 10)
    #print exec_cmd("sleep 1", 2)
    #print exec_cmd("sleep 5", 2)
    #print exec_cmd("dkfjlksjfsdlkf", 2)




