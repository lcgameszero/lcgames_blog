$(document).ready(function(){

    var nowDate = new Date();

    $("#textDate").datetimepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayBtn: true,
        startView:2,
        minView:2,
        maxView:2,
        language:"zh-CN"
    });
    //$("#textDate").datetimepicker("setStartDate",nowDate);

    var sw = window.screen.width;
    var sh = window.screen.height;
    var chartInverted = true;
    if (sw > sh) {
        chartInverted = false;
    }
    console.log(sw,sh,chartInverted);

    var myChart = null;
    var showChart = function(labels1,datas1,labels2,datas2,selectChartType){
        if (!chartInverted) {
            labels1.reverse();
            datas1.reverse();
            labels2.reverse();
            datas2.reverse();
        }
        var labelPerfix = '房源数量 / ';
        var shortPrefix = '数量/';
        if (selectChartType == "day") {
            labelPerfix = labelPerfix + "日";
            shortPrefix = shortPrefix + "日";
        } else if (selectChartType == "week") {
            labelPerfix = labelPerfix + "周";
            shortPrefix = shortPrefix + "周";
        } else if (selectChartType == "month") {
            labelPerfix = labelPerfix + "月";
            shortPrefix = shortPrefix + "月";
        } else if (selectChartType == "year") {
            labelPerfix = labelPerfix + "年";
            shortPrefix = shortPrefix + "年";
        }

        var no_repeat_shortPrefix = shortPrefix;
        shortPrefix = no_repeat_shortPrefix+" (重复)";
        if (myChart) {
            //myChart.remove();
            myChart.destroy();
            myChart = null;
        }
        myChart = Highcharts.chart('chartContainer', {
            chart: {
                type: 'areaspline',
                inverted: chartInverted
            },
            title: {
                text: '深圳市二手房源公示'
            },
            subtitle: {
                text:'数据来源: http://ris.szpl.gov.cn/bol/EsSource.aspx'
            },
            colors: ['#dddddd', '#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9', 
                '#f15c80', '#e4d354', '#2b908f', '#f45b5b', '#91e8e1'],
            xAxis: {
                categories: labels1
            },
            yAxis: {
                title: {
                    text: labelPerfix
                },
                labels: {
                    formatter: function () {
                        return this.value;
                    }
                },
                min: 0
            },
            plotOptions: {
                area: {
                    fillOpacity: 0.5
                },
                areaspline: {
                    dataLabels: {
                        enabled: true
                    },
                    enableMouseTracking: false
                }
            },
            series: [{
                name: shortPrefix,
                data: datas1
            },{
                name: no_repeat_shortPrefix,
                data: datas2
            }]
        });
    };

    var selectChartType = "week";
    var first_enter = true;
    var getChartDatas = function(type) {
        data = {'type':selectChartType};
        $.ajax({
            type: 'POST',
            url: '/search_estates',
            data: JSON.stringify(data),
            contentType: 'application/json; charset=UTF-8',
            dateType: 'json',
            success: function(data) {
                var labels1 = [];
                var labelDatas1  = [];
                var labelDatas2  = [];
                //console.log("labels:",labels);
                //console.log("labelDatas:",labelDatas);
                for (var index = 0; index < data.length; index++) {
                    var d = data[index];
                    if (selectChartType == "day") {
                        labels1.push(d.label.slice(5));
                    } else if (selectChartType == "week") {
                        labels1.push(d.label);
                    } else if (selectChartType == "month") {
                        labels1.push(d.label.slice(0,7));
                    } else if (selectChartType == "year") {
                        labels1.push(d.label.slice(0,4));
                    }
                    labelDatas1.push(parseInt(d.num));
                    labelDatas2.push(parseInt(d.no_repeat_num));
                }

                showChart(labels1,labelDatas1,labels1.concat(),labelDatas2,selectChartType);
            },
            error: function(data) {
                console.log('error');
            }
        });
    };

    var toggleDiv = function(target) {
        $("ul li[role=presentation]").removeClass('active');
        var id = target.attr("id");
        target.addClass("active");

        $("#estatesDiv").hide();
        $("#chartDiv").hide();
        $("#msgDiv").hide();
        if (id == "navEstates") {
            $("#estatesDiv").show();
        } else if (id == "navChart") {
            $("#chartDiv").show();
            if (first_enter) {
                first_enter = false
                getChartDatas(selectChartType);
            }
        } else if (id == "navMsg") {
            $("#msgDiv").show();
        }
    };

    toggleDiv($("#navEstates"));

    $("ul li[role=presentation]").on("click",function(e){
        toggleDiv($(e.currentTarget));
    });

    $(".dropdown .dropdown-menu li").on("click",function(e){
        var target = $(e.currentTarget);
        var type = target.attr("value");

        $("#dropdownMenu1").empty();
        if (type == "day") {
            $("#dropdownMenu1").append($('<font>房源数量/日&nbsp;&nbsp;</font><span class="caret"></span>'));
        } else if (type == "week") {
            $("#dropdownMenu1").append($('<font>房源数量/周&nbsp;&nbsp;</font><span class="caret"></span>'));
        } else if (type == "month") {
            $("#dropdownMenu1").append($('<font>房源数量/月&nbsp;&nbsp;</font><span class="caret"></span>'));
        } else if (type == "year") {
            $("#dropdownMenu1").append($('<font>房源数量/年&nbsp;&nbsp;</font><span class="caret"></span>'));
        }

        selectChartType = type;
        getChartDatas(selectChartType);
    });

    //getChartDatas(selectChartType);

    $("#textDate").datetimepicker().off("changeDate");
    $("#textDate").datetimepicker().on('changeDate', function(ev){
        console.log('date-change')
    });

    $("#btnSearch").off("click");
    $("#btnSearch").on("click", function(e){
        $("#formSearch").submit();
    });

    $("#btnDetail").off("click");
    $("#btnDetail").on("click", function(e){
        //$("#formSearch").submit();
        //alert('功能开发中')
    });

    var setEstateDetail = function(e) {
        console.log(e)
        $("#txtSid_form").attr('value',e.sid);
        $("#txtName_form").attr('value',e.name);
        $("#txtCsn_form").attr('value',e.csn);
        $("#txtZone_form").attr('value',e.zone);
        $("#txtSpace_form").attr('value',e.space+"㎡");
        $("#txtFloor_form").attr('value',e.floor);
        $("#txtUsage_form").attr('value',e.usage);
        $("#txtSn_form").attr('value',e.sn);
        $("#txtProxy_form").attr('value',e.proxy);
    }

    //打开界面获取最新信息
    $("#modalDetail").on("show.bs.modal",function(event){
        var btn = $(event.relatedTarget);
        var tmp = btn.data("whatever");
        var sid = parseInt(tmp.slice("detail_".length));
        data = {}
        $.ajax({
            type: 'GET',
            url: '/estates/'+sid,
            data: JSON.stringify(data),
            contentType: 'application/json; charset=UTF-8',
            dateType: 'json',
            success: function(data) {
                setEstateDetail(data);
            },
            error: function(data) {
                console.log('error');
            }
        });
    });
});