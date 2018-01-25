#!/usr/bin/env bash
netstat -nap|grep ":$1 "|grep ESTAB|wc -l