function formatDate(dateValue) { //
    var time = new Date(parseInt(dateValue) * 1000);
    var ymdhis = "";
    ymdhis += time.getFullYear() + "-";
    ymdhis += Appendzero((time.getMonth()+1)) + "-";
    ymdhis += Appendzero(time.getDate());
    ymdhis += " " + Appendzero(time.getHours()) + ":";
    ymdhis += Appendzero(time.getMinutes()) + ":";
    ymdhis += Appendzero(time.getSeconds());
    return ymdhis;
};

function formatDate() { //
    var time = new Date();
    var ymdhis = "";
    ymdhis += time.getFullYear() + "-";
    ymdhis += Appendzero((time.getMonth()+1)) + "-";
    ymdhis += Appendzero(time.getDate());
    ymdhis += " " + Appendzero(time.getHours()) + ":";
    ymdhis += Appendzero(time.getMinutes()) + ":";
    ymdhis += Appendzero(time.getSeconds());
    return ymdhis;
};

function formatDateCompat(dateValue) {
    var time = new Date(parseInt(dateValue) * 1000);
    var ymdhis = "";
    ymdhis += time.getFullYear();
    ymdhis += Appendzero((time.getMonth()+1));
    ymdhis += Appendzero(time.getDate());
    ymdhis += " " + Appendzero(time.getHours());
    ymdhis += Appendzero(time.getMinutes());
    ymdhis += Appendzero(time.getSeconds());
    return ymdhis;
}

function Appendzero(obj){
    if(obj<10) return "0" +""+ obj;
    else return obj;
}

var HostList = san.defineComponent({
    template: ''
    + '<div class="folder" id="hosts">'
    + '<div class="folder-title" on-click="toggle">host count:{{count}} - till: {{ts}}</div>'
    + '<div class="folder-main" style="{{fold ? \'display:none\' : \'\'}}">'
    + '<dl san-for="h in hosts" title="hh{{h}}">{{h}}</dl>'
    + '</div>'
    + '</div>',
    toggle: function () {
        this.data.set('fold', !this.data.get('fold'));
    },
    computed:{
        count: function() {
            return this.data.get('hosts').length
        }
    },
    initData: function() {
        return {
            hosts: [],
            fold: true
        }
    },
    updateModel: function(model) {
        this.data.set('hosts', model)
        this.data.set('count', model.length)
        this.data.set('ts', formatDate())
    }
});


var LightZone = san.defineComponent({
    template: ''
    + '<div class="{{color}}-folder">'
    + '<div class="{{color}}-folder-title" on-click="toggle">{{color|upper}} light count: {{count}}</div>'
    + '<div class="folder-main" s-if="count>0" style="{{fold ? \'display:none\' : \'\'}}">'
    + '<table class="{{color}}-table">'
    + '      <tr>'
    + '          <th>时间</th>'
    + '          <th>名称</th>'
    + '          <th>对象</th>'
    + '          <th>描述</th>'
    + '          <th>开始时间</th>'
    + '      </tr>'
    + '      <tr s-for="l in lights">'
    + '          <td>{{ l.lastTs }}</td>'
    + '          <td>{{ l.name }}</td>'
    + '          <td>{{ l.obj }}</td>'
    + '          <td>{{ l.desc }}</td>'
    + '          <td>{{ l.createTs }}</td>'
    + '      </tr>'
    + '  </table>'
    + '</div>'
    + '</div>',
    toggle: function () {
        this.data.set('fold', !this.data.get('fold'));
    },
    computed:{
        count: function() {
            return this.data.get('lights').length
        }
    },
    initData: function() {
        return {
            color: "red",
            lights: [],
            fold: true
        }
    },
    updateModel: function(lights) {
        var l = Object.values(lights)
        for(var i in l) {
            l[i].createTs = formatDateCompat(l[i].createTs)
            l[i].alarmTs= formatDateCompat(l[i].alarmTs)
            l[i].lastTs= formatDateCompat(l[i].lastTs)
        }
        this.data.set('lights', l)
        if (this.data.get('fold') && this.data.get('count')>0) {
            this.toggle()
        }
    }
});

var Folder = san.defineComponent({
    template: ''
    + '<div class="{{prefix}}-folder">'
    + '<div class="{{prefix}}-folder-title" on-click="toggle">{{title}}</div>'
    + '<div class="{{prefix}}-folder-main" style="{{fold ? \'display:none\' : \'\'}}">'
    + '<slot></slot>'
    + '</div>'
    + '</div>',
    toggle: function () {
        this.data.set('fold', !this.data.get('fold'));
    },
    initData: function() {
        return {
            'fold': true
        }
    }
});

var HostDetail = san.defineComponent({
    components: {
        'ui-folder': Folder
    },
    template: ''
    + '<div>'
    + '<ui-folder prefix="hostdetail" san-for="h in hostdetail" title="{{h.hostname}}">'
    + '<ui-folder prefix="stat" title="STAT COUNT: {{h.states.length}}">'
    + '<table class="stat-table">'
    + '      <tr>'
    + '          <th>时间</th>'
    + '          <th>名称</th>'
    + '          <th>对象</th>'
    + '          <th>状态</th>'
    + '          <th>描述</th>'
    + '      </tr>'
    + '      <tr s-for="l in h.states">'
    + '          <td>{{ l.ts}}</td>'
    + '          <td>{{ l.name }}</td>'
    + '          <td>{{ l.id }}</td>'
    + '          <td>{{ l.msg }}</td>'
    + '          <td>{{ l.state }}</td>'
    + '      </tr>'
    + '  </table>'
    + '</ui-folder>'
    + '<ui-folder prefix="kpi" title="KPI COUNT: {{h.kpis.length}}">'
    + '<table class="kpi-table">'
    + '      <tr>'
    + '          <th>时间</th>'
    + '          <th>名称</th>'
    + '          <th>对象</th>'
    + '          <th>值</th>'
    + '      </tr>'
    + '      <tr s-for="l in h.kpis">'
    + '          <td>{{ l.ts}}</td>'
    + '          <td>{{ l.name }}</td>'
    + '          <td>{{ l.id}}</td>'
    + '          <td>{{ l.value}}</td>'
    + '      </tr>'
    + '  </table>'
    + '</ui-folder>'
    + '</ui-folder>'
    + '</div>',
    updateModel: function(model) {
        var hostdetail =  [];
        var hosts = Object.keys(model)
        for (i=0;i<hosts.length;i++) {
            var host = hosts[i]
            var kpis = []
            for (j=0;j<model[host].kpis.length;j++) {
                var kpi = model[host].kpis[j]
                kpis.push({
                    id: kpi.id,
                    name: kpi.name,
                    ts: formatDate(kpi.data.ts),
                    value: kpi.data.value
                })
            }
            var stats = []
            for (j=0;j<model[host].states.length;j++) {
                var stat = model[host].states[j]
                stats.push({
                    id: stat.id,
                    name: stat.name,
                    ts: formatDate(stat.data.ts),
                    state: function() {
                        if (stat.data.stat==0) {
                            return "正常"
                        } else {
                            return "异常("+stat.data.stat+")"
                        }
                    }(),
                    msg : stat.data.msg
                })
            }

            hostdetail.push({
                hostname: host,
                kpis: kpis,
                states: stats
            })
        }
        this.data.set("hostdetail", hostdetail)
        var host_folder = this.ref('host_folder')
        if (host_folder) {
            host_folder.data.set('count', 1)
            host_folder.data.set('fold', false)
        }
    },
})
