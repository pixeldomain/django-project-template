from fabric.api import local

projectname = "{{ project_name }}"


def startapp():
    local("sudo supervisorctl restart {{ project_name }}")
    local("sudo nginx -s reload")
