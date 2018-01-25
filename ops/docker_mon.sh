#!/bin/bash

image=daocloud.io/library/centos:6.8
docker run --restart always --name ryb_indexer -v /data/ryb_mon:/ryb_mon --net host -d -w /ryb_mon/bin  ${image} ./indexer
docker run --restart always --name ryb_agent -v /data/ryb_mon:/ryb_mon --net host -d -w /ryb_mon/bin  ${image} ./agent
docker run --restart always --name ryb_detector -v /data/ryb_mon:/ryb_mon --net host -d -w /ryb_mon/bin  ${image} ./detector
docker run --restart always --name ryb_notifier -v /data/ryb_mon:/ryb_mon --net host -d -w /ryb_mon/bin  ${image} ./notifier
docker run --restart always --name ryb_web -v /data/ryb_mon:/ryb_mon --net host -d -e OMC_AUTH=paco,eric7777:admin,eric6666 -w /ryb_mon/bin  ${image} ./webapp

