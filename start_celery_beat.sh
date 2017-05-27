. env/bin/activate
echo start celery beat ...
nohup celery beat -A celery_runner -l info --pidfile /tmp/web_blog/celery_beat.pid >>/tmp/web_blog/celery_beat.log 2>&1 &
sleep 1s
echo start celery beat success...
deactivate