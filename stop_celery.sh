echo stop celery...
echo stop celery beat ...
`cat /tmp/web_blog/celery_beat.pid | awk '{print "kill -9 " $1}'`
echo stop celery worker ...
`cat /tmp/web_blog/celery_worker.pid | awk '{print "kill -9 " $1}'`
echo stop celery flower ...
`netstat -ntlp | grep 0.0.0.0:5555 | awk '{print $7}' | awk -F / '{print "kill -9 " $1}'`
echo stop celery success...