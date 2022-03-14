import re
from subprocess import run
from pydantic import BaseModel
from pydantic.fields import T
from scripts.common.cvs import GitRepository
import os
from fastapi import HTTPException, Request
from . import run_cmd
from .ansible import AnsibleAPI, write_host
from scripts.logger import logger
from loguru import logger as base_logger
import os
import time


class ProjectInfo(BaseModel):
    git_url: str
    base_dir: str = "/data/back_apps"
    host: str
    pre_script: str
    start_script: str
    name: str


class ClientAliyun(BaseModel):
    project_name: str
    version: str
    type: str = "res"
    unzip: bool = False
    filename: str


def create_deploy_log(uuid):
    basedir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(basedir, 'logs')

    if not os.path.exists(log_path):
        os.mkdir(log_path)
    log_path_deploy = os.path.join(log_path, f'{uuid}_deploy.log')
    base_logger.add(log_path_deploy, retention="20 days")
    return base_logger


async def deploy_service(request: Request, project: ProjectInfo, tag: str,
                         uuid: str):
    client = request.app.state.redis
    dd = await client.set('x_token')
    yaml_files = "./playbook/1.yaml"
    deploy_log = create_deploy_log(uuid)
    tag_files = build_project(project, deploy_log, tag)
    if tag_files:
        run_data = {"source": tag_files}
        deploy_log = create_deploy_log(uuid)
        if publish_remote(project.host, yaml_files, run_data, deploy_log):
            logger.info(f"deploy {project.name} with {tag} success!")
        else:
            logger.error(f"push remote failed!")
    else:
        logger.error("git failed")


async def sync_aliyun(clientinfo: ClientAliyun):
    if not clientinfo:
        logger.error(f"{clientinfo} some config error!")
    if not clientinfo.unzip:
        if clientinfo.project_name and clientinfo.version:
            cmd = '''ssh 10.10.2.2 "source /etc/profile && cd /data/scripts/ && python3 sync_cdn_aliyun.py -p {project_name} -v {version} -t {type}"'''.format(
                **clientinfo)
            logger.info(f"start cmd={cmd}")
            os.system(cmd)
            return True
        else:
            return False
    else:
        if clientinfo.filename:
            clientinfo.version = clientinfo.filename.split('.')[0]
            if clientinfo.filename.endswith('.zip'):
                unzip_cmd = '''ssh 10.10.2.2 "cd /data/ftp/data/{project_name} && /usr/bin/unzip -uoq {filename} && chown -R ftpuser. {version}"'''.format(
                    **clientinfo)
                logger.info(f"unzip cmd={unzip_cmd}")
                os.system(unzip_cmd)
                sync_cmd = '''ssh 10.10.2.2 "source /etc/profile && cd /data/scripts/ && python3 sync_cdn_aliyun.py -p {project_name} -v {version} -t {type}"'''.format(
                    **clientinfo)
                logger.info(f"sync aliyun with {sync_cmd}")
                os.system(sync_cmd)
                return True
            else:
                logger.error(f"filename ={clientinfo.filename} not define!")
                return False

    logger.info(f"sync clinet {clientinfo}")


@logger.trace
def build_project(project: ProjectInfo, deploy_log: logger, tag: str):
    # git clone
    local_path = project.base_dir + '/' + tag
    #print(local_path, project.git_url, tag)
    try:
        git = GitRepository(local_path=local_path, repo_url=project.git_url)
        git.pull()
        git.change_to_tag(tag)
        deploy_log.debug(f"git files from {project.name}")
    except:
        logger.error(f"git {project.name} failed")
        deploy_log.error(f"git {project.name} failed")
        return False

    # run pre scripts
    out, status = run_cmd(project.pre_script)
    if not status:
        return False
    # find tag files
    tag_files = "1.tag.gz"
    return tag_files


@logger.trace
def publish_remote(host: str, yaml_files: str, run_data: dict,
                   deploy_log: logger):
    # run ansible-play deloy tag files && run start script in remote
    hosts = write_host(host)
    an = AnsibleAPI(hosts)
    run_out = an.run_playbook(yaml_files, run_data)
    print(run_out)
    if re.findall('error', run_out):
        deploy_log.error(f"deploy failed")
        deploy_log.error(run_out)
        return False
    else:
        deploy_log.info(run_out)
        return True
