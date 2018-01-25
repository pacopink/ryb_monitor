#!/usr/bin/python
#coding: utf8
#对传入的url发送http请求,判断返回值是否为200来确定是否web服务正常
import urllib
import urllib2
import sys
import socket
from urllib2 import HTTPError

url = sys.argv[1] #"http://221.180.247.78/lbs_web/probe/host.jsp"

urllib2.socket.setdefaulttimeout(2) #期待2s内有返回
if url[0:4].lower() != "http":
    url = "http://"+url


def conn():
    try:
        code = urllib2.urlopen(url).getcode()
        if code == 200:
            sys.stdout.write("url[{url}] ok".format(url=url))
            sys.exit(0)
        else:
            sys.stdout.write("url[{url}] respond[{code}]".format(url = url, code=code))
            sys.exit(1)
    except urllib2.URLError,e:
        sys.stdout.write("url[{url}] exception[{excp}]".format(url = url, excp=e))
        sys.exit(1)
    except socket.timeout, e:
        raise e
    except Exception, e:
        raise e
        sys.stdout.write("url[{url}] exception[{excp}]".format(url = url, excp=e))
        sys.exit(1)

if __name__=="__main__":
    try:
        try:
            conn()
        except socket.timeout, e:  #如果超时,重试一次
                conn()
    except Exception, e:
        sys.stdout.write("url[{url}] exception[{excp}]".format(url = url, excp=e))
        sys.exit(1)

