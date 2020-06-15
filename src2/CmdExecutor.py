#!/usr/bin/env python
#coding:utf-8

import os
import threading
import time

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


def get_output_lines(cmd):
    '''get huge volumn of outputs'''
    with os.popen(cmd) as p:
        for l in p:
            yield l

def generate_script_file(path, cmd, sub_cmds):
    with open(path, 'w') as f:
        f.write(cmd)
        f.write("<<__EOF__\n")
        f.write(sub_cmds)
        if sub_cmds[-1:] != "\n":
            f.write("\n")
        f.write("__EOF__")
        f.write("\n")


if __name__=='__main__':
    import sys
    from SocketLock import *
    @withLockWait
    def do():
        FILE="/tmp/xxx.sh"
        print exec_cmd("rm -rf "+FILE, 10)
        generate_script_file(FILE, "/opt/bin/cls", "aaa\nbbbb\ncccc\ncommit\nexit\n")
        for l in get_output_lines("cat "+FILE):
            sys.stderr.write(l)
        print exec_cmd("sh "+FILE, 10)
    do()
