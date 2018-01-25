# RYG Monitor文档
说明： 本md基于有道云笔记的版本编写

## 背景
为了及时发现系统故障,全面掌控系统状态,开发一个轻量级的分布式主机监控系统.
## 设计目标
zabbix等太多外部依赖,和对特定业务的定制,所以决定重新设计一个轻量级的监控系统，满足如下目标：
- 通用化,不针对特定的业务场景
- 开放接口,通过开放的agent上报接口和可配置的监控主机和obj指标获取方式,让RYG_Monitor能够广泛适应各种中小型系统的监控.
- 使用Redis做为存储和消息总线,这是唯一的一个依赖中间件,不再需要任何其他中间件和RMDBS
- 纯Python实现,兼容RHEL6的Python2.6环境和RHEL7的Python2.7,发布包应该包含需要的第三方库,应对用户不能联网的内网服务器环境.
- 轻量级agent,作为一个简单的调度框架,调度probe脚本获取obj上报indexer,合理的资源占用
- 微服务化,把agent,indexer,detector,notifier, webapp等完全解耦,通过JSON over HTTP以及Redis作为总线整合起来, 每一块都可以单独部署和定制,灵活应对部署环境.
- 通过Digest鉴权,保证访问的合法性
- 基于Linux/Unix
## 业务模型

### 数据模型
```
graph LR
    state-->|belongs to|host
    kpi-->|belongs to|host
    host-->|+stateId or +kpiId|obj
    obj-->|stores in|obj_history
    obj_history-->|get head|light
    light-->|include|red_light
    light-->|include|yellow_light
    light-->|include|green_light
    red_light-->|turns into|alarm
    green_light-->|if red b4, turns into|clear
    alarm-->|send to recv|notification
    clear-->|send to recv|notification
```

### 术语表

术语 | 说明
---|---
state | 状态，由一个id标识，如a1.0001, 状态取值只有0和非0,<br/>0 表示正常，非0表示不正常，<br/>还有一个msg参数附加一些不正常时候的额外信息，<br/>另外有一个ts时间戳表示状态更新的时间
kpi | 指标，由一个id标识，如k2.0017,<br/>取值value只有正整数，<br/>另外有一个ts时间戳表示指标上报时间
probe|一个脚本,agent会定期调度获取state和kpi用于上报
host| 表示一个受控主机，由hostname标识，<br/>带有一个states列表和kpi列表表示本主机会上报的状态和kpi.
obj|对某主机上一个state,kpi的统称<br/>由[STAT\|KPI]:[hostname]:[stateId\|kpiId]标识,<br/>这个标识，称为objId
obj历史list|以objId为key，存放在redis里面的一个list，<br/>按时间顺序入队列，定期清理超过保留范围的object记录，<br/>list的第一个元素代表的是现状。
light|信号灯，逻辑上有red(红灯)，yellow(黄灯)，green(绿灯)，<br/>由detector扫描系统所有obj之后，决定会有什么灯。
red light|如果一个state的取值为非0或者最近上报超过3个上报周期，挂红灯<br/>如果一个kpi设置了max，min值，而实际取值超过了范围，挂红灯
yellow light|如果一个KPI超过3个上报周期没上报，<br/>或者某个obj完全没有上报历史，挂黄灯
green light|如果一个stat和kpi，不符合上面红灯，黄灯的条件，则是绿灯。
alarm|系统根据red light的情况，<br/>以及对应red light的alarmInterval，<br/>来触发告警到告警队列。
clear|当一个obj从红灯变为绿灯时,<br/>如果触发过alarm并且needClear设置为true,<br/>则触发一个clear到告警队列
notification|由notifier从告警队列中获取告警或者clear,<br/>然后根据objId, 查询已经配置的recv group,<br/>获取recv的集合做短信触发,也可以改造支持其他方式的触发.
recv|notification接受者的号码
recv group|notification接受者组,用于和某个objId的前缀关联,<br/>这样当符合这个前对的obj告警到来时,能找到这个组做发送



## 系统组件
### 架构图
```
graph TD
m((host1))-->|IF1: collect indexes|agent1
agent1-->|IF2: report indexes|indexer
mX((hostX))-->|IF1: collect indexes|agentX
agentX-->|IF2: report indexes|indexer
indexer-->|save to|r((Redis))
r-->|scan for lights|detector
detector-->|enqueue alarm/clear|r
r-->|dequeue alarm/clear|notifier
r-->|retrieve system summary|webapp
webapp-->|IF3: http api|b((browser))
```
### agent 受控主机代理
根据本主机的hostname,从conf.yml中查找到本主机需要监控的state和kpi列表,根据配置定期执行
### indexer 管理端接收器
包含了一个httpd线程和若干个indexer线程,通过进程内消息队列,以producer-consumer方式工作
- httpd 单线程运行,接收IF1接口送过来的状态报告,做合法性检查后,入到队列中
- indexer 多线程运行,从队列中获取状态报告,索引到Redis中
### detector  管理端监控器
根据conf.yml中配置的所有主机的states和kpis列表,构造出需要扫描检查的object列表,
以定期轮询方式,获取所有object的现状,然后根据配置分类到红黄绿灯,更新Redis的灯状态.对于红灯,按条件触发告警,对于恢复到绿灯的红灯,按条件触发清除告警到Redis中的告警队列.
### notifier  管理端告警发送器
监听Redis中的告警队列,取出对告警发布信息后,根据告警的objId获得stateId或者kpiId,到recv.yml中找到匹配对应id前缀的接收用户组,触发通知短信.
### web 系统状况展示界面
提供HTTP API,从Redis中,获取系统状态.
提供用户友好的展示页面,供用户在浏览器中查询系统状态.

## 系统接口
### IF1:监控脚本
对应于配置在conf.yml中的state和kpi的probe,脚本的实际位置存放在script_path配置项中.监控脚本并不指定需要使用的语言,可以是shell, perl, python或者语言编译出来的可执行文件,只要符合如下条件
- 在agent的子进程环境下可执行
- 如果是state的监控脚本,return_code作为state的状态,stdout输出作为msg
- 如果是kpi的监控脚本,当return_code为0时,把stdout转为一个整形作为kpi的value
- 脚本会根据interval配置频繁调度,共享进程池所以应尽量避免长时间的block和重量级的操作
### IF2:受控主机状态上报HTTP API
这是一个JSON over HTTP接口,通过POST方式提交到<br/>URL: /indexer/report<br/> body样例如下
上报请求样例
```javascript
{
  "hostname": "hp",    //主机hostname
  "ts": 1516687375     //Unix秒钟数时间戳
  "kpi": [             //上报KPI列表
    {
      "id": "k0.0001", 
      "value": 372
    }
  ], 
  "state": [           //上报STATE列表
    {
      "msg": "OK", 
      "stat": 0, 
      "id": "a1.0001"
    }, 
    {
      "msg": "OK", 
      "stat": 0, 
      "id": "a1.0002"
    }
  ], 
}
```
Indexer给Agent的响应消息,根据HTTP Response Code如果是200表示成功,如果是503表示Indexer内部队列满,可以尝试重试,404表示消息不合法或者hostname未注册,可以从body中的JSON获取进一步情况.
```javascript
{
  "msg": "ok", 
  "stat": 0
}
```
### IF3:Indexer WebService API
#### 获取整个系统的简要状态
- API<br/>
/getSummary/
- Example<br/>
GET /getSummary
- 样例返回<br/>
```javascript
{
  "hosts": [
    "hp", 
    "hp2"
  ], 
  "lights": {
    "red": {
      "KPI:hp:k0.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665498, 
        "createTs": 1516615098, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "KPI:hp:k0.0001 状态连续3个周期未更新，请检查", 
        "name": "proc_number", 
        "needClear": true, 
        "obj": "KPI:hp:k0.0001"
      }, 
      "STAT:hp:a1.0002": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665514, 
        "createTs": 1516615113, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "STAT:hp:a1.0002 状态连续3个周期未更新，请检查", 
        "name": "webapp3", 
        "needClear": true, 
        "obj": "STAT:hp:a1.0002"
      }
    }, 
    "yellow": {
      "STAT:hp2:a1.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 0, 
        "createTs": 1516594717, 
        "desc": "None", 
        "lastTs": 1516668950, 
        "msg": "no stat reported yet, please check", 
        "name": "webapp1", 
        "needClear": true, 
        "obj": "STAT:hp2:a1.0001"
      }
    }
  }
}
```

#### 获取整个系统的详细状态
在获取系统简要状态的URL上,加上参数detail=1,会在返回对象中,得到一个detail属性,该属性包含了以主机名为key的各个主机的详细状态报告,包括红绿灯和所有state,kpi的最新状态.
- API<br/>
/getSummar/
- Example<br/>
GET /getSummary?detail=1
- 样例返回<br/>
```javascript
{
  "hosts": [          //系统所有受监控主机列表
    "hp", 
    "hp2", 
  ], 
  "lights": {         //系统所有灯信号列表,包括红灯黄灯列表
    "red": {
      "KPI:hp:k0.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665498, 
        "createTs": 1516615098, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "KPI:hp:k0.0001 状态连续3个周期未更新，请检查", 
        "name": "proc_number", 
        "needClear": true, 
        "obj": "KPI:hp:k0.0001"
      }, 
      "STAT:hp:a1.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665514, 
        "createTs": 1516615113, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "STAT:hp:a1.0001 状态连续3个周期未更新，请检查", 
        "name": "webapp1", 
        "needClear": true, 
        "obj": "STAT:hp:a1.0001"
      }, 
      "STAT:hp:a1.0002": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665514, 
        "createTs": 1516615113, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "STAT:hp:a1.0002 状态连续3个周期未更新，请检查", 
        "name": "webapp3", 
        "needClear": true, 
        "obj": "STAT:hp:a1.0002"
      }
    }, 
    "yellow": {
      "STAT:hp2:a1.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 0, 
        "createTs": 1516594717, 
        "desc": "None", 
        "lastTs": 1516668950, 
        "msg": "no stat reported yet, please check", 
        "name": "webapp1", 
        "needClear": true, 
        "obj": "STAT:hp2:a1.0001"
      }, 
      "STAT:hp2:a1.0002": {
        "alarmInterval": 3600, 
        "alarmTs": 0, 
        "createTs": 1516594717, 
        "desc": "None", 
        "lastTs": 1516668950, 
        "msg": "no stat reported yet, please check", 
        "name": "webapp3", 
        "needClear": true, 
        "obj": "STAT:hp2:a1.0002"
      } 
    }
  },
  "details": {       //按主机区分的状体报告列表,每个主机的状态结构,见下一节的描述
    "hp2": {
      "kpis": [], 
      "lights": {
        "red": {}, 
        "yellow": {
          "STAT:hp2:a1.0001": {
            "alarmInterval": 3600, 
            "alarmTs": 0, 
            "createTs": 1516594717, 
            "desc": "None", 
            "lastTs": 1516668950, 
            "msg": "no stat reported yet, please check", 
            "name": "webapp1", 
            "needClear": true, 
            "obj": "STAT:hp2:a1.0001"
          }, 
          "STAT:hp2:a1.0002": {
            "alarmInterval": 3600, 
            "alarmTs": 0, 
            "createTs": 1516594717, 
            "desc": "None", 
            "lastTs": 1516668950, 
            "msg": "no stat reported yet, please check", 
            "name": "webapp3", 
            "needClear": true, 
            "obj": "STAT:hp2:a1.0002"
          }
        }
      }, 
      "states": []
    }, 
    "hp": {
      "kpis": [
        {
          "data": {
            "ts": 1516842553, 
            "value": 19
          }, 
          "id": "KPI:hp:k0.0001", 
          "name": "proc_number"
        }, 
        {
          "data": {
            "ts": 1516842552, 
            "value": 243
          }, 
          "id": "KPI:hp:k1.0001", 
          "name": "cpu_usage"
        }, 
        {
          "data": {
            "ts": 1516842555, 
            "value": 481
          }, 
          "id": "KPI:hp:k1.0002", 
          "name": "mem_usage"
        }, 
        {
          "data": {
            "ts": 1516842555, 
            "value": 277
          }, 
          "id": "KPI:hp:k1.0003", 
          "name": "disk_usage"
        }
      ], 
      "lights": {
        "red": {
          "KPI:hp:k0.0001": {
            "alarmInterval": 3600, 
            "alarmTs": 1516665498, 
            "createTs": 1516615098, 
            "desc": "状态连续3个周期未更新", 
            "lastTs": 1516668950, 
            "msg": "KPI:hp:k0.0001 状态连续3个周期未更新，请检查", 
            "name": "proc_number", 
            "needClear": true, 
            "obj": "KPI:hp:k0.0001"
          }, 
          "STAT:hp:a1.0001": {
            "alarmInterval": 3600, 
            "alarmTs": 1516665514, 
            "createTs": 1516615113, 
            "desc": "状态连续3个周期未更新", 
            "lastTs": 1516668950, 
            "msg": "STAT:hp:a1.0001 状态连续3个周期未更新，请检查", 
            "name": "webapp1", 
            "needClear": true, 
            "obj": "STAT:hp:a1.0001"
          }, 
          "STAT:hp:a1.0002": {
            "alarmInterval": 3600, 
            "alarmTs": 1516665514, 
            "createTs": 1516615113, 
            "desc": "状态连续3个周期未更新", 
            "lastTs": 1516668950, 
            "msg": "STAT:hp:a1.0002 状态连续3个周期未更新，请检查", 
            "name": "webapp3", 
            "needClear": true, 
            "obj": "STAT:hp:a1.0002"
          }
        }, 
        "yellow": {}
      }, 
      "states": [
        {
          "data": {
            "msg": "OK", 
            "stat": 0, 
            "ts": 1516777564
          }, 
          "id": "STAT:hp:a1.0001", 
          "name": "webapp1"
        }, 
        {
          "data": {
            "msg": "OK", 
            "stat": 0, 
            "ts": 1516777565
          }, 
          "id": "STAT:hp:a1.0002", 
          "name": "webapp3"
        }, 
        {
          "data": {
            "msg": "url[http://127.0.0.1/webapp2/probe/host.jsp] ok", 
            "stat": 0, 
            "ts": 1516842556
          }, 
          "id": "STAT:hp:a9.0001", 
          "name": "webapp2外网心跳"
        }
      ]
    }
  }
}

```
#### 获取某个主机的状态
用于获得特定主机的状态报告,等同于系统详细报告的detail属性的对应主机报告.
- API<br/>
/getSummary/<hostname>
- Example<br/>
GET /getSummary/hp
- 样例返回<br/>
```javascript
{
  "kpis": [
    {
      "data": {
        "ts": 1516842553, 
        "value": 19
      }, 
      "id": "KPI:hp:k0.0001", 
      "name": "proc_number"
    }, 
    {
      "data": {
        "ts": 1516842552, 
        "value": 243
      }, 
      "id": "KPI:hp:k1.0001", 
      "name": "cpu_usage"
    }, 
    {
      "data": {
        "ts": 1516842555, 
        "value": 481
      }, 
      "id": "KPI:hp:k1.0002", 
      "name": "mem_usage"
    }, 
    {
      "data": {
        "ts": 1516842555, 
        "value": 277
      }, 
      "id": "KPI:hp:k1.0003", 
      "name": "disk_usage"
    }
  ], 
  "lights": {
    "red": {
      "KPI:hp:k0.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665498, 
        "createTs": 1516615098, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "KPI:hp:k0.0001 状态连续3个周期未更新，请检查", 
        "name": "proc_number", 
        "needClear": true, 
        "obj": "KPI:hp:k0.0001"
      }, 
      "STAT:hp:a1.0001": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665514, 
        "createTs": 1516615113, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "STAT:hp:a1.0001 状态连续3个周期未更新，请检查", 
        "name": "webapp1", 
        "needClear": true, 
        "obj": "STAT:hp:a1.0001"
      }, 
      "STAT:hp:a1.0002": {
        "alarmInterval": 3600, 
        "alarmTs": 1516665514, 
        "createTs": 1516615113, 
        "desc": "状态连续3个周期未更新", 
        "lastTs": 1516668950, 
        "msg": "STAT:hp:a1.0002 状态连续3个周期未更新，请检查", 
        "name": "webapp3", 
        "needClear": true, 
        "obj": "STAT:hp:a1.0002"
      }
    }, 
    "yellow": {}
  }, 
  "states": [
    {
      "data": {
        "msg": "OK", 
        "stat": 0, 
        "ts": 1516777564
      }, 
      "id": "STAT:hp:a1.0001", 
      "name": "webapp1"
    }, 
    {
      "data": {
        "msg": "OK", 
        "stat": 0, 
        "ts": 1516777565
      }, 
      "id": "STAT:hp:a1.0002", 
      "name": "webapp3"
    }, 
    {
      "data": {
        "msg": "url[http://127.0.0.1/webapp2/probe/host.jsp] ok", 
        "stat": 0, 
        "ts": 1516842556
      }, 
      "id": "STAT:hp:a9.0001", 
      "name": "webapp2外网心跳"
    }
  ]
}
```

#### 获取某个Obj的历史记录,按时间倒排序
- API <br/>
/getObjHistory/<objId>/<count> <br/><br/>
- Example<br/>
GET /getObjHistory/STAT:hp:a1.0001/3<br/>
- 样例返回
```javascript
{
  "dataList": [
    {
      "ts": 1516842555, 
      "value": 481
    }, 
    {
      "ts": 1516842544, 
      "value": 481
    }, 
    {
      "ts": 1516842534, 
      "value": 481
    }
  ], 
  "id": "KPI:hp:k1.0002", 
  "name": "mem_usage"
}
```


