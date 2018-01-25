#!/bin/env python
#coding: utf8
from flask import Flask, render_template, jsonify, request, make_response, url_for, redirect
from flask_digest import Stomach

from service import *


def create_app():
  app = Flask(__name__)
  app.config['JSON_AS_ASCII'] = False
  stomach = Stomach(__name__)
  return (app, stomach)

app, stomach = create_app()


db=dict()
@stomach.register
def add_user(username, password):
    db[username] = password

@stomach.access
def get_user(username):
    return db.get(username, None)


@app.route("/getSummary/")
@app.route("/getSummary/<string:hn>")
@stomach.protect
def getSystemSummary(hn='all'):
    detailFlag = False
    if hn=='all' and request.args.get("detail", '0') in ['1', 1, 'true']:
        detailFlag =True
    return jsonify(getSummary(hn, detailFlag))

@app.route("/getObjHistory/<string:objId>/<int:count>")
@stomach.protect
def getStatHistory(objId, count):
    return jsonify(getObjHistory(objId, count))

@app.route("/")
def index():
    return app.send_static_file('index.html')
    


if __name__=="__main__":
    import os
    #env sample : export RYG_AUTH=paco,123456:admin:123456
    auth_str = os.environ.get('RYG_AUTH')
    if auth_str is None:
        add_user('admin', '123456') #not good practice, just for test
    else:
        map(lambda x:add_user(*x),
            map(lambda x:x.split(','),
                auth_str.split(':')))
    app.run(host="0.0.0.0", port=38888, debug=True)


