import time
import getpass
from fabric.api import env, roles, execute, run, sudo, puts
from fabric.context_managers import cd, settings, prefix
from fabric.contrib.files import append
from fabric.contrib.console import confirm


# Get Mac username and use it for sudo actions
USERNAME = ''.join(ch for ch in getpass.getuser() if ch.isalnum())

### Configuration options start. ###
PROJECT_NAME = '{{project_name}}'  # Dir name that contains the settings dir
PROJECT_REPO = 'git@github.com:pixeldomain/{{project_name}}.git'
SERVER = 'pixeldomain.co.uk'
DOMAIN = '{{project_name}}.pixeldomain.co.uk'
GUNICORN_PORT = '80??'
#USERNAME = ''  # use if your local login is not the same as remote
### Configuration options end. ###

VIRTUAL_ENVS = '/home/production/venv'

env.user = 'production'
env.roledefs = {
    'web_workers': [SERVER, ],
    'database': [SERVER, ],
    'sudo_actions': ['{0}@{1}'.format(USERNAME, DOMAIN), ]
}
env.root_path = '/home/production/public_html/{0}'.format(PROJECT_NAME)


def deploy():
    """Deploys to the live server."""

    # Setup
    env.release = time.strftime('%Y%m%d%H%M%S')
    deployment_tasks = []

    # Options
    opt_initial = confirm('Is this the initial deployment?', default=False)
    if not opt_initial:
        opt_update_deps = confirm('Update pip dependencies?', default=False)

    opt_migrate_database = confirm('Sync and migrate database?', default=False)
    opt_take_offline = False
    if opt_migrate_database:
        opt_take_offline = confirm(('Take site offline during '
                                    'sync and migration?'), default=True)

    opt_restart_web_workers = confirm('Restart web workers?', default=True)

    # Queue up deployment tasks
    if opt_initial:
        deployment_tasks.append(initial_deployment)
        deployment_tasks.append(create_supervisor_config)
        deployment_tasks.append(create_gunicorn_config)
    else:
        deployment_tasks.append(get_latest_release)
        if opt_update_deps:
            deployment_tasks.append(update_dependencies)

        if not confirm('Preparation complete, continue?', default=True):
            return

        if opt_migrate_database:
            if opt_take_offline:
                deployment_tasks.append(stop_web_workers)
            deployment_tasks.append(symlink_current_release)
            deployment_tasks.append(sync_and_migrate)
        else:
            deployment_tasks.append(symlink_current_release)

        deployment_tasks.append(collect_static)

        if opt_restart_web_workers or opt_take_offline:
            if opt_take_offline:
                deployment_tasks.append(start_web_workers)
            else:
                deployment_tasks.append(restart_web_workers)

    # Run tasks
    for task in deployment_tasks:
        execute(task)


@roles('web_workers')
def update_dependencies():
    with cd('{0}/source/requirements'.format(env.root_path)):
        with prefix('source {0}/{1}/bin/activate'.format(
                VIRTUAL_ENVS, PROJECT_NAME)):
            run('pip install -r production.txt')


@roles('web_workers')
def initial_deployment():
    """Initial deployment tasks.

    Create the required directories, checkout the source code and install
    dependencies.
    """

    run('mkdir {0}'.format(env.root_path))
    with cd(env.root_path):
        run('mkdir config')
        run('mkdir releases')
        run('mkdir releases/current')
        run('mkdir releases/previous')
        run('mkdir media')
        run('mkdir static')
        run('git clone {0} source'.format(PROJECT_REPO))

    with cd(VIRTUAL_ENVS):
        run('virtualenv {0}'.format(PROJECT_NAME))

    update_dependencies()


@roles('web_workers')
def get_latest_release():
    """Get the latest stable version of the code.

    Create an archive from the current Git master branch and place in folder
    then symlink folders
    """

    run('mkdir {0}/releases/{1}'.format(env.root_path, env.release))
    with cd('{0}/source'.format(env.root_path)):
        run('git pull origin master')
        run('git archive master | tar -xm -C {0}/releases/{1}'.format(
            env.root_path, env.release))

    run('ln -s /home/production/public_html/{0}/media '
        '/home/production/public_html/{1}/releases/{2}/src/'.format(
            PROJECT_NAME, PROJECT_NAME, env.release))
    run('ln -s /home/production/public_html/{0}/static '
        '/home/production/public_html/{1}/releases/{2}/src/'.format(
            PROJECT_NAME, PROJECT_NAME, env.release))


@roles('web_workers')
def symlink_current_release():
    """Symlink Release to live folder."""

    with settings(warn_only=True):
        with cd('{0}'.format(env.root_path)):
            run('rm releases/previous -R')
            run('mv releases/current releases/previous')
            run('ln -s {0} releases/current'.format(env.release))


@roles('database')
def sync_and_migrate():
    """Sync and migrate the database."""

    with cd('{0}/releases/current/src'.format(env.root_path)):
        with prefix('source {0}/{1}/bin/activate'.format(
                VIRTUAL_ENVS, PROJECT_NAME)):
            run('python manage.py syncdb '
                '--noinput '
                '--settings={0}.settings.live'.format(PROJECT_NAME))

            # Only show migration warnings for some reason it kicks up a fuss
            with settings(warn_only=True):
                run('python manage.py migrate '
                    '--settings={0}.settings.live'.format(PROJECT_NAME))


@roles('web_workers')
def collect_static():
    """Run manage.py collectstatic."""

    with cd('{0}/releases/{1}/src'.format(env.root_path, env.release)):
        with prefix('source {0}/{1}/bin/activate'.format(
                VIRTUAL_ENVS, PROJECT_NAME)):
            run('python manage.py collectstatic '
                '--noinput '
                '--settings={0}.settings.live'.format(PROJECT_NAME))


@roles('sudo_actions')
def stop_web_workers():
    sudo('supervisorctl stop {0}'.format(PROJECT_NAME))


@roles('sudo_actions')
def start_web_workers():
    sudo('supervisorctl start {0}'.format(PROJECT_NAME))


@roles('sudo_actions')
def restart_web_workers():
    sudo('supervisorctl reload')


@roles('sudo_actions')
def create_supervisor_config():
    config = """[program:%(project)s]
directory = /home/production/public_html/%(project)s/releases/current/src
user = production
command = /home/production/public_html/%(project)s/config/gunicorn.sh
stdout_logfile = /home/production/logs/logfile_supervisor_%(project)s
stderr_logfile = /home/production/logs/errlog_supervisor_%(project)s
""" % ({'project': PROJECT_NAME})
    path = '/etc/supervisor/conf.d/{0}.conf'.format(PROJECT_NAME)
    append(path, config, use_sudo=True)
    sudo('supervisorctl reload')


@roles('web_workers')
def create_gunicorn_config():
    config = """#!/bin/bash
set -e

LOGFILE=/home/production/logs/logfile_gunicorn_%(project)s
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=3
# user/group to run as
USER=production
GROUP=webmaster
ADDRESS=127.0.0.1:%(port)s
DJANGO_SETTINGS_MODULE=%(project)s.settings.live

cd /home/production/public_html/%(project)s/releases/current/src
source /home/production/venv/%(project)s/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

exec gunicorn %(project)s.wsgi:application \\
  --workers=$NUM_WORKERS \\
  --bind=$ADDRESS \\
  --user=$USER --group=$GROUP \\
  --log-level=debug \\
  --error-logfile=$LOGFILE
""" % ({'project': PROJECT_NAME, 'port': GUNICORN_PORT})
    path = '/home/production/public_html/{0}/config/gunicorn.sh'.format(
        PROJECT_NAME)
    append(path, config)
    run('chmod +x {0}'.format(path))
    puts('Now create the database and set the environment variables.')
