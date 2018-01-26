#!/usr/bin/python
#coding: utf8
#对传入的url发送http请求,判断返回值是否为200来确定是否web服务正常
import urllib
import urllib2
import sys

url = sys.argv[1]

urllib2.socket.setdefaulttimeout(2) #期待2s内有返回
if url[0:4].lower() != "http":
    url = "http://"+url

def conn(retry=2):
    try:
        code = urllib2.urlopen(url).getcode()
        if code == 200:
            sys.stdout.write("url[{url}] ok".format(url=url))
            sys.exit(0)
        else:
            sys.stdout.write("url[{url}] respond[{code}]".format(url = url, code=code))
            sys.exit(1)
    except Exception, e:
        if retry>0:
            return conn(retry-1)
        else:
            sys.stdout.write("url[{url}] exception[{excp}]".format(url = url, excp=e))
            sys.exit(1)

if __name__=="__main__":
    conn()

