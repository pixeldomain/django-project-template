from fabric.api import local, env, run


HOSTS = ['']
SERVER_USER = 'production'


def startapp():
    local("sudo supervisorctl restart {{ project_name }}")
    local("sudo nginx -s reload")


def production():
    env.hosts = HOSTS
    env.user = SERVER_USER


def production_deploy():
    run('cd /home/production/public_html/{{ project_name }}; git pull')
