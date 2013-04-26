#!/bin/bash
set -e
LOGFILE=/home/production/logs/logfile_gunicorn_{{ project_name }}
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=3
USER=production
GROUP=production
ADDRESS=127.0.0.1:8001
cd /home/production/public_html/{{ project_name }}/src/
source /home/production/virtualenv/{{ project_name }}/bin/activate
test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn_django -w $NUM_WORKERS --bind=$ADDRESS \
  --user=$USER --group=$GROUP --log-level=debug \
  --log-file=$LOGFILE 2>>$LOGFILE