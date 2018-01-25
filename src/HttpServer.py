#!/bin/env python
#coding:utf8

import traceback
from flask import Flask,jsonify,abort, make_response,request
import json
import Queue
from werkzeug.serving import make_server
import threading
from Entity import *
from Logger import *


def create_flask_app(mon_hosts, queue):
    app = Flask("indexer")
    @app.route('/indexer/report', methods=['POST'])
    def recv_report():
        #j = request.get_data()
        try:
            src_ip = str(request.remote_addr)
            j = request.get_data()
            log_debug("recv_report: [%s]", j)
            try:
                report = AgentReportMsg.fromJson(j)
            except Exception, e:
                log_warn("failed to process report [%s]", j)
                print traceback.format_exc()
                x = jsonify({"stat":-1, "msg": e.__str__()})
                x.headers["Content-Type"] = "application/json; charset=utf-8"
                return make_response(x, 404)

            #检查Hostname是否在监控列表，否则回404
            if (report["hostname"] not  in mon_hosts):
                log_warn("hostname[%s] is not registered in config file, discard resport [%s]", report["hostname"], j)
                x = jsonify({"stat":9, "msg":"invalid hostname"})
                x.headers["Content-Type"] = "application/json; charset=utf-8"
                return make_response(x, 404)
            #检查IP是否跟配置一致，否则也拒绝
            hostname = report["hostname"]
            if ("ip"  in mon_hosts[hostname] and  src_ip!=(mon_hosts[hostname]["ip"])):
                log_warn("ip [%s] of hostname[%s] is not match [%s] that configured in config file, discard resport [%s]", src_ip, hostname, mon_hosts[hostname]['ip'], j)
                x = jsonify({"stat":9, "msg":"invalid ip"})
                x.headers["Content-Type"] = "application/json; charset=utf-8"
                return make_response(x, 404)

            #一切正常，加入处理队列，并返回200
            queue.put_nowait(report)
            log_info("enqueue report from [%s] ok", hostname)
            x = jsonify({"stat":0, "msg":"ok"})
            x.headers["Content-Type"] = "application/json; charset=utf-8"
            return x
        except Queue.Full: #队列满，返回503，知识客户端重试
            log_warn("queue full, discard received msg and respond 503")
            x = jsonify({"stat":1, "msg":"indexer busy please retry later"})
            x.headers["Content-Type"] = "application/json; charset=utf-8"
            return make_response(x, 503)
        except Exception,e:
            print traceback.format_exc()
            abort(500)
    app.config['JSON_AS_ASCII'] = False
    return app
    #app.run(host=center_host, port=center_port,debug=True)

class HttpServerThread(threading.Thread):
    def __init__(self, host, port, mon_hosts, queue):
        threading.Thread.__init__(self)
        app = create_flask_app(mon_hosts, queue)
        self.srv = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()
        log_info("HttpServer shutdown")

