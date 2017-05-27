. env/bin/activate
echo start celery worker ...
nohup celery worker -A celery_runner -l info --pidfile /tmp/web_blog/celery_worker.pid >>/tmp/web_blog/celery_worker.log 2>&1 &
sleep 1s
echo start celery worker success ...
deactivate