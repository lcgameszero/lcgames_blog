# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from . import estate
from .. import db
from ..models import SzEstate
import urllib
import os
import time
import math
from datetime import datetime,date
import requests
from bs4 import BeautifulSoup
import chardet

initCached = False
max_cache_num = 1000
sz_cache = {}
#房源公示
@estate.route('/sz', methods=['GET','POST'])
#@login_required
def sz():
    formDate = None
    formZone = None
    formSN = None
    if request.method == 'POST':
        if 'textDate' in request.form:
            formDate = request.form['textDate'].lstrip().rstrip()
        if 'textZone' in request.form:
            formZone = request.form['textZone'].lstrip().rstrip()
        if 'textSn' in request.form:
            formSN = request.form['textSn'].lstrip().rstrip()
    #print formDate,formZone,formSN
    #初次使用系统,初始化缓存
    global initCached
    global initCheckProcess
    global sz_cache
    if not initCached:
        initCached = True
        initCache()
     #准备首页数据
    today = datetime.today()
    #当天时间
    curDayString = '%d-%02d-%02d' % (today.year,today.month,today.day)
    #没有任何一个参数则默认显示今天
    if not formDate and not formZone and not formSN:#
        formDate = curDayString

    #搜索结果
    estates = searchEstates(formDate,formZone,formSN)
    if not estates:
        estates = []
    return render_template("estate/sz_estate.html",curDayString=curDayString,formDate=formDate,curEstates=estates)

#更新房源
@estate.route('/update_sz', methods=['GET'])
@login_required
def update_sz():
    #doCheck()
    return redirect(url_for('estate.sz'))

#初始化缓存
@estate.route('/cache_sz', methods=['GET'])
@login_required
def cache_sz():
    initCache()
    return redirect(url_for('estate.sz'))

#根据条件搜索
def searchEstates(date,zone,sn,no_repeat=True):
    global sz_cache
    es = sz_cache.get(date)

    #当日的数据强制重刷
    today = datetime.today()
    curDayString = '%d-%02d-%02d' % (today.year,today.month,today.day)
    if curDayString == date:
        es = None
    arr = []
    #sn是否为数字
    isSnNum = True
    if sn:
        try:
            int(sn)
        except:
            isSnNum = False

    if not es:
        #无缓存,全部数据从数据库取得
        #print 'search 1'
        if date and zone and sn:
            if isSnNum:
                es = SzEstate.query.filter_by(pub_date=date).filter_by(zone=zone).filter_by(sn=sn).all()
            else:
                es = SzEstate.query.filter_by(pub_date=date).filter_by(zone=zone).filter(SzEstate.name.like('%'+sn+'%')).all()
        elif zone and sn:
            if isSnNum:
                es = SzEstate.query.filter_by(zone=zone).filter_by(sn=sn).all()
            else:
                es = SzEstate.query.filter_by(zone=zone).filter(SzEstate.name.like('%'+sn+'%')).all()
        elif date and sn:
            if isSnNum:
                es = SzEstate.query.filter_by(pub_date=date).filter_by(sn=sn).all()
            else:
                es = SzEstate.query.filter_by(pub_date=date).filter(SzEstate.name.like('%'+sn+'%')).all()
        elif date and zone:
            es = SzEstate.query.filter_by(pub_date=date).filter_by(zone=zone).all()
        elif date:
            es = SzEstate.query.filter_by(pub_date=date).all()
        elif zone:
            es = SzEstate.query.filter_by(zone=zone).all()
        elif sn:
            if isSnNum:
                es = SzEstate.query.filter_by(sn=sn).all()
            else:
                es = SzEstate.query.filter(SzEstate.name.like('%'+sn+'%')).all()
        
        #包装数据
        for e in es:
            ee = {'sid':e.sid,'name':e.name,'csn':e.csn,'zone':e.zone,'space':e.space,'usage':e.usage,'floor':e.floor,'sn':e.sn,'proxy':e.proxy,'pub_date':e.pub_date}
            arr.append(ee)
            analyzeEstate(ee)
    elif zone or sn:
        #有缓存且有zone或sn条件,从缓存中搜索
        #print 'search 2'
        for e in es:
            if zone and sn and zone == e.get('zone') and sn == e.get('sn'):
                arr.append(e)
            elif zone and zone == e.get('zone'):
                arr.append(e)
            elif sn and sn == e.get('sn'):
                arr.append(e)
    else:
        #无zone或sn条件
        #print 'search 3'
        arr = es

    #筛选重复的房源
    if no_repeat:
        no_repeat_arr = []
        no_repeat_keys = []
        for e in arr:
            esn = e.get('sn')
            if not esn or no_repeat_keys.count(esn) > 0:
                continue
            no_repeat_keys.append(esn)
            no_repeat_arr.append(e)

        return no_repeat_arr
    return arr

#获取指定参数房源   page:页数 zone:区域 tep_name:项目名称
retry_error = 0
max_retry_error = 5
def getEstates(page,zone="",tep_name=""):
    global retry_error
    global max_retry_error
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 UBrowser/6.1.2107.204 Safari/537.36'
    values = {'targetpage' : page, 'zone' : zone, 'tep_name' : tep_name}
    headers = {'User-Agent' : user_agent}
    data = urllib.urlencode(values)
    #print "data:",data
    url = '%s%s%s' % ('http://ris.szpl.gov.cn/bol/EsSource.aspx','?',data)
    print url
    html = None
    try:
        html = requests.get(url, headers=headers)
    except Exception,e:
        print Exception,":",e
        retry_error = retry_error + 1
        if retry_error < max_retry_error:
            #发生错误重新尝试,最多max_retry_error次
            print "retry count:%d %d %s %s" % (retry_error,page,zone,tep_name)
            getEstates(page,zone,tep_name)
        return []
    #解析html
    es = parse_html(html.content)
    retry_error = 0
    return es

#解析数据
def parse_html(html):
    objs = []
    #print 'html:',html
    charset_obj = chardet.detect(html)
    #print 'html charset',charset_obj
    soup = BeautifulSoup(html,'html5lib',from_encoding=charset_obj['encoding'])
    table = soup.find('table',id='DataGrid1')
    trs = []
    if table:
        trs = table.find_all('tr')
    #print "parse len:",len(trs)
    if len(trs) > 0:
        trs = trs[1:]
        for tr in trs:
            tds = tr.find_all('td')
            #sid
            sid = tds[0].find('a')['onclick']
            sid = sid[sid.find('(')+1:sid.find(')')]
            #项目名称   招商路北住宅楼18栋
            name = tds[0].find('a').string
            #合同流水号  (2017)第21090号
            csn = tds[1].string
            #区属 南山
            zone = tds[2].string
            #面积(㎡)  75.40
            space = tds[3].string
            #用途 多层铝窗住宅
            usage = tds[4].string
            #楼层 
            floor = tds[5].string
            #房源编码
            sn = tds[6].string
            #代理中介名称
            proxy = tds[7].find('a').string
            foid = tds[7].find('a')['href']
            #中介电话
            proxy_phone = tds[7].string
            #发布日期
            pub_date = tds[8].string

            obj = {'sid':sid,'name':name,'csn':csn,'zone':zone,'space':space,'usage':usage,'floor':floor,'sn':sn,'proxy':proxy,'proxy_phone':proxy_phone,'pub_date':pub_date}
            objs.append(obj)
            #print obj
            #print "%s %s %s" % (sid,pub_date,sn)
    objs.reverse()
    return objs

def hasUpdate(updates,sid):
    for e in updates:
        if e.get('sid') == sid:
            return True
    return False

#实际检查更新函数
def doCheck(cached=True):
    loop = True
    page = 1
    updates = []
    while loop:
        es = getEstates(page)
        #降序
        es.reverse()
        page = page + 1
        loop = False
        count = 0
        update_arr = []
        no_update_arr = []
        for e in es:
            count = count + 1
            sz_es = SzEstate.query.filter_by(sid=e.get('sid')).first()
            if not sz_es:
                #插入到第一个
                if not hasUpdate(updates,e.get('sid')):
                    update_arr.append(e.get('sid',''))
                    updates.insert(0,e)
                else:
                    no_update_arr.append(e.get('sid',''))
                #第一个如果也是更新的房源,则去寻找下一页
                if count == len(es):
                    print 'doCheck next page:',page
                    loop = True

        print "update_arr:",update_arr
        print "no_update_arr:",no_update_arr
        
    #更新数据库
    for e in updates:
        estate = SzEstate()
        estate.sid=int(e.get('sid',''))
        estate.name=e.get('name','')
        estate.csn=e.get('csn','')
        estate.zone=e.get('zone','')
        estate.space=float(e.get('space',''))
        estate.usage=e.get('usage','')
        estate.floor=e.get('floor','')
        estate.total_floor=e.get('total_floor','')
        estate.sn=e.get('sn','')
        estate.proxy=e.get('proxy','')
        estate.pub_date=e.get('pub_date','')
        db.session.add(estate)
        if cached:
            pushCache(e)
    #提交事务
    update_num = len(updates)
    if update_num > 0:
        db.session.commit()
        #排序并检查数量
        sortCache()
        checkCacheNum()

    return update_num

#初始化所有数据
def initEstates(maxPage = None, delay = 0.5):
    total_num = getEstatesNum()
    total_num = int(total_num)
    print 'total_num:',total_num
    if not maxPage:
        maxPage = math.floor(total_num/20)
        maxPage = int(maxPage)+1
    print 'maxPage:',maxPage
    for i in range(maxPage):
        time.sleep(delay)
        page = maxPage-i
        print 'proccess page:',page
        if page < 1:
            print 'proccess complete:',page
            break
        es = getEstates(page)
        for e in es:
            sz_es = SzEstate.query.filter_by(sid=e.get('sid')).first()
            if not sz_es:
                estate = SzEstate()
                estate.sid=int(e.get('sid',''))
                estate.name=e.get('name','')
                estate.csn=e.get('csn','')
                estate.zone=e.get('zone','')
                estate.space=float(e.get('space',''))
                estate.usage=e.get('usage','')
                estate.floor=e.get('floor','')
                estate.total_floor=e.get('total_floor','')
                estate.sn=e.get('sn','')
                estate.proxy=e.get('proxy','')
                estate.pub_date=e.get('pub_date','')
                db.session.add(estate)
        #提交事务
        db.session.commit()

#获取记录数量
def getEstatesNum():
    global retry_error
    global max_retry_error
    user_agent = 'Mozilla/4.0 (compatibl; MSIE 5.5; Windows NT)'
    values = {'targetpage' : 1, 'zone' : '', 'tep_name' : ''}
    headers = {'User-Agent' : user_agent}
    data = urllib.urlencode(values)
    url = '%s%s%s' % ('http://ris.szpl.gov.cn/bol/EsSource.aspx','?',data)
    html = None
    try:
        html = requests.get(url, headers=headers)
    except Exception,e:
        print Exception,":",e
        retry_error = retry_error + 1
        if retry_error < max_retry_error:
            #发生错误重新尝试,最多max_retry_error次
            print "retry count:%d %d %s %s" % (retry_error,page,zone,tep_name)
            getEstatesNum()
        return 0
    
    charset_obj = chardet.detect(html.content)
    soup = BeautifulSoup(html.content,'html5lib',from_encoding=charset_obj['encoding'])
    span_a1s = soup.find_all('span',class_='a1')
    span_a1 = None
    if len(span_a1s) > 1:
        span_a1 = span_a1s[1]
    num = 0
    if span_a1:
        num = int(span_a1.string[2:-4])
    retry_error = 0
    return num

#初始化缓存
def initCache():
    global sz_cache
    del sz_cache
    sz_cache = {}
    sz_es = SzEstate.query.all()
    total = len(sz_es)
    sz_es = sz_es[total-max_cache_num:total]
    for e in sz_es:
        ee = {'sid':e.sid,'name':e.name,'csn':e.csn,'zone':e.zone,'space':e.space,'usage':e.usage,'floor':e.floor,'sn':e.sn,'proxy':e.proxy,'pub_date':e.pub_date}
        pushCache(ee)

    #排序
    sortCache()
    print '---------------initCache',len(sz_es)

#获取最大和最小日期
def getCacheLimitDate():
    global sz_cache
    max,min = None,None
    for k in sz_cache:
        if not max:
            min = max = k
        if k > max:
            max = k
        if k < min:
            min = k
    return max,min

#统计缓存数量
def countCache():
    count = 0
    for k in sz_cache:
        count = count + len(sz_cache[k])
    return count

#删除时间最早的一个房源,也就是sid最小的一个
def delMinEstate(arr):
    min = None
    for e in arr:
        if not min:
            min = e
        if e.get('sid') < min.get('sid'):
            min = e
    
    if min:
        print 'remove cache date:',min.get('pub_date')
        arr.remove(min)

#为缓存排序
def sortCache(date=None):
    print 'sortCache',date
    for k in sz_cache:
        if k == date or not date:
            arr = sz_cache[k]
            arr.sort(sortCompare)

#排序算法
def sortCompare(e1,e2):
    if e1.get('sid')>e2.get('sid'):
        return -1
    return 1

#分析房源
def analyzeEstate(estate):
    #暂不分析
    #todo
    return
    es = SzEstate.query.filter_by(sn=estate.get('sn')).all()
    arr = []
    for e in es:
        if e.sid != estate.get('sid'):
            ee = {'sid':e.sid,'name':e.name,'csn':e.csn,'zone':e.zone,'space':e.space,'usage':e.usage,'floor':e.floor,'sn':e.sn,'proxy':e.proxy,'pub_date':e.pub_date}
            arr.append(ee)
    estate['same'] = arr
    estate['new'] = True
    for e in arr:
        if e.get('pub_date') < estate.get('pub_date'):
            estate['new'] = False

#插入数据到缓存
def pushCache(e,check = False):
    global sz_cache
    global max_cache_num
    pub_date = e.get('pub_date',None)
    if pub_date:
        arr = sz_cache.get(pub_date,None)
        if not arr:
            arr = []
            sz_cache[pub_date] = arr
            print 'add cache date:',pub_date
        analyzeEstate(e)
        arr.append(e)
    
    if check:
        #排序
        sortCache(pub_date)
        checkCacheNum()

#检查并维持缓存大小
def checkCacheNum():
    count = countCache()
    #print 'cache count start:',count
    if count > max_cache_num:
        maxDate,minDate = getCacheLimitDate()
        delMinEstate(sz_cache[minDate])
    count = countCache()
    #print 'cache count end:',count
    #if count > max_cache_num:
        #checkCacheNum()
