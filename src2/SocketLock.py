#!/bin/env python
#coding:utf8
'''通过打开一个本地的UDP端口,来检测是否有相同的程序在运行'''

from socket import *

# 指定一个UDP端口号用于互斥
PORT = 64444

class LockTimeoutException(Exception):
    '''LockTimeoutException'''
    def __str__(self):
        return 'LockTimeoutException'

class LockAcquireFailException(Exception):
    '''lock acquire failed'''
    def __str__(self):
        return 'LockAcquireFailException'

class LockNotHolderToReleaseException(Exception):
    '''if I am not the lock holder and a release is revoked'''
    def __str__(self):
        return 'LockAcquireFailException'

class SocketLock:
    def __init__(self, port=PORT):
        self.addr = ("127.0.0.1", port)
        self.s = None

    def acquire_nonblock(self):
        '''acuiqre lock without blocking'''
        if self.s is not None:
            return
        try:
            self.s = socket(AF_INET, SOCK_DGRAM)
            # not allow socket reuse
            self.s.setsockopt(SOL_SOCKET,SO_REUSEADDR, 0)
            self.s.bind(self.addr)
            return
        except Exception,e:
            self.s = None
            #log_debug(e)
            raise LockAcquireFailException()

    def acquire_block(self, second=20):
        import time
        span = 0.1
        tick = int(second/span)
        print_flag = False
        while True:
            try:
                self.acquire_nonblock()
                return
            except LockAcquireFailException:
                pass
            tick -= 1
            if tick<0:
                break
            if not print_flag:
                # only print this line once
                print "waiting lock for {SECOND} seconds ...".format(SECOND=second)
                print_flag = True
            try:
                time.sleep(span)
            except Exception:
                break
        raise LockTimeoutException()

    def release(self):
        '''release the holding lock'''
        if self.s is not None:
            self.s.close()
            self.s = None
        else:
            raise LockNotHolderToReleaseException()

def withLockWait(second=20):
    def wrapper0(fun):
        '''decorator of function with blocking lock'''
        def wrapper(*args, **kargs):
            lock = SocketLock()
            lock.acquire_block(second)
            ret = fun(*args, **kargs)
            lock.release()
            return ret
        return wrapper
    return wrapper0

def withLock(fun):
    '''decorator of function with nonblocking lock'''
    def wrapper(*args, **kargs):
        lock = SocketLock()
        lock.acquire_nonblock()
        ret = fun(*args, **kargs)
        lock.release()
        return ret
    return wrapper
        
if __name__=="__main__":
    import threading
    import time
    from Logger import *

    # 通过装饰器让这个do方法被锁保护，12表示等待的时间是12s，超过12s获取不到锁就抛出异常
    @withLockWait(12)
    def do(name, sleep):
        log_info("enter: "+ name)
        time.sleep(sleep)
        log_info("exit: "+ name)
        time.sleep(0.01)

    def doIt(name, sleep):
        try:
            do(name, sleep)
        except Exception,e:
            log_error(name+":"+str(e))

    # 并发若干个线程，争抢锁资源, 按等待时常，其中至少有一个必然抢不到
    tt = map(lambda x:threading.Thread(target=doIt, args=x), 
            [("thread-1", 5), 
                ("thread-2", 5), 
                ("thread-3", 6), 
                ("thread-4", 6), 
                ("thread-5", 5)]
            )
    map(lambda x:x.start(), tt)
    map(lambda x:x.join(), tt)





