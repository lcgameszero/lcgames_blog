# -*- coding: utf-8 -*-
import os
from app import create_app
from celery import Celery
from celery_tasks import log,update_estates

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )

    celery.conf.update(app.config)
    #celery.config_from_object('celeryconfig')
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery

flask_app = create_app(os.getenv('FLASK_CONFIG') or 'default')
celery = make_celery(flask_app)
