echo start celery...
#工作进程
. start_celery_worker.sh
sleep 4s
#Flower celery任务监控
. start_celery_flower.sh
sleep 1s
#定时任务工作进程
. start_celery_beat.sh
echo start celery success...