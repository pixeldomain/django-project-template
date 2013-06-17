from fabric.api import local, env, run


HOSTS = ['']
SERVER_USER = 'production'


def startapp():
    local("sudo supervisorctl restart {{ project_name }}")
    local("sudo nginx -s reload")


def aws():
    env.hosts = HOSTS
    env.user = SERVER_USER


def aws_deploy():
    run('cd /mnt/ebs/public_html/{{ project_name }}; git pull')
