import yaml
from Indexer import Indexer
from conf import RygConf
import Queue
reportQueue = Queue.Queue(200)
from HttpServer import HttpServerThread
import time
from Logger import *

if __name__=="__main__":
    log_info("start indexer ...")
    cfgFile="../conf/conf.yml"
    conf = RygConf.load(cfgFile)
    httpd = HttpServerThread(conf.center_host, conf.center_port, conf.mon_hosts, reportQueue)
    httpd.start()
    log_info("httpd thread started" )
    processors = list()
    for i in xrange(0, conf.threads):
        p = Indexer(reportQueue, conf)
        p.start()
        processors.append(p)
    log_info("processor threads started")
    #endless loop until terminated, do healthy check termly
    while True:
        if not httpd.isAlive():
            log_critical("HTTPD thread exited, terminate for restart")
            break
        errorFlag = False
        for p in processors:
            if not p.isAlive():
                errorFlag = True
                break
        if errorFlag:
            log_critical("ReportProcessor thread exited, terminate for restart")
            break
        try:
            time.sleep(1)
        except:
            break
    httpd.shutdown()
    httpd.join(3)
    log_info("httpd thread exited")
    for p in processors:
        p.terminate()
    for p in processors:
        p.join()
    log_info("processor threads exited")
    log_info("indexer stopped")
