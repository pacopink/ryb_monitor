#!/bin/env python
#coding:utf8
'''通过打开一个本地的UDP端口,来检测是否有相同的程序在运行,用于agent'''

from socket import *
s = socket(AF_INET, SOCK_DGRAM) #socket的引用需要保持才能锁住,所以不能在函数里面
def acquire(port=54444):
    s.bind(('localhost', port))

if __name__=="__main__":
    acquire()
    s2 = socket(AF_INET, SOCK_DGRAM)
    s2.bind(('localhost', 54444))
