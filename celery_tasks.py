# -*- coding: utf-8 -*-
from app import celery
from app.estate.views import doCheck,countCache
from manage import app

@celery.task()
def log(msg):
    return msg

@celery.task(bind=True)
def update_estates(self,args):
    update_num = -1

    with app.app_context():
        cache_num = countCache()
        print 'update_estates before:%s %x' % (cache_num,id(app))
        update_num = doCheck()
        cache_num = countCache()
        print 'update_estates after:%s %x' % (cache_num,id(app))

    return {"num":update_num}