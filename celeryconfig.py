# -*- coding: utf-8 -*-
from datetime import timedelta
from celery.schedules import crontab
# Broker and Backend
#BROKER_URL = 'redis://127.0.0.1:6379'
#CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@localhost:5672//'
# Timezone
CELERY_TIMEZONE='Asia/Shanghai'    # 指定时区，不指定默认为 'UTC'
# CELERY_TIMEZONE='UTC'
# import
CELERY_IMPORTS = (
    'celery_tasks.log',
    'celery_tasks.update_estates'
)
# schedules
CELERYBEAT_SCHEDULE = {
    'update_estates_every_1_hours' : {
        'task': 'celery_tasks.update_estates',
        'schedule': datetime.timedelta(seconds=60*15),
        'args': ([],)
    },
    'log_every_30_seconds' : {
        'task': 'celery_tasks.log',
        'schedule': datetime.timedelta(seconds=30*1000),
        'args': ('Message',)
    }''',
    'multiply-at-some-time': {
        'task': 'celery_app.task2.multiply',
        'schedule': crontab(hour=9, minute=50),   # 每天早上 9 点 50 分执行一次
        'args': (3, 7)                            # 任务函数参数
    }'''
}