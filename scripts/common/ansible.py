#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
import json
import pdb
import copy
import time


def write_host(ip_addr):
    host_file = "%s/host%s" % ('/tmp', time.strftime("%Y%m%d%H%M%s"))
    with open(host_file, 'a+') as f:
        for x in ip_addr.split(','):
            f.writelines(x + '\n')
    return host_file


class ResultsCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultsCallback, self).__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_unreachable = {}
        self.task_failed = {}
        self.task_skipped = {}
        self.task_stats = {}
        # self.host_ok = {}
        # self.host_unreachable = {}
        # self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self.task_skipped[result._host.get_name()] = result

    def v2_runner_on_stats(self, result, *args, **kwargs):
        self.task_stats[result._host.get_name()] = result


class AnsibleAPI(object):
    def __init__(self, hostfile, *args, **kwargs):
        self.loader = DataLoader()
        self.results_callback = ResultsCallback()
        # if not os.path.isfile(hostfile):
        #     raise Exception("%s file not found!" % hostfile)
        self.inventory = InventoryManager(
            loader=self.loader, sources=[hostfile])
        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory)
        self.passwords = None
        Options = namedtuple('Options',
                             ['connection',
                              'remote_user',
                              'ask_sudo_pass',
                              'verbosity',
                              'ack_pass',
                              'module_path',
                              'forks',
                              'become',
                              'become_method',
                              'become_user',
                              'check',
                              'listhosts',
                              'listtasks',
                              'listtags',
                              'syntax',
                              'sudo_user',
                              'sudo',
                              'diff'])
        # 初始化需要的对象
        self.options = Options(connection='smart',
                               remote_user=None,
                               ack_pass=None,
                               sudo_user=None,
                               forks=5,
                               sudo=None,
                               ask_sudo_pass=False,
                               verbosity=5,
                               module_path=None,
                               become=None,
                               become_method=None,
                               become_user=None,
                               check=False,
                               diff=False,
                               listhosts=None,
                               listtasks=None,
                               listtags=None,
                               syntax=None)

    @staticmethod
    def deal_result(info):
        host_ips = list(info.get('success').keys())
        info['success'] = host_ips

        error_ips = info.get('failed')
        error_msg = {}
        for key, value in error_ips.items():
            temp = {}
            temp[key] = value.get('stderr')
            error_msg.update(temp)
        info['failed'] = error_msg
        return info
        # return json.dumps(info)

    def run(self, module_name, module_args):
        play_source = dict(
            name="Ansible Play",
            hosts='all',
            gather_facts='no',
            tasks=[
                dict(action=dict(module=module_name, args=module_args),
                     register='shell_out'),
                # dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback,
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        # 定义字典用于接收或者处理结果
        result_raw = {'success': {}, 'failed': {},
                      'unreachable': {}, 'skipped': {}, 'status': {}}

        # 循环打印这个结果，success，failed，unreachable需要每个都定义一个
        for host, result in self.results_callback.task_ok.items():
            result_raw['success'][host] = result._result
        for host, result in self.results_callback.task_failed.items():
            result_raw['failed'][host] = result._result
        for host, result in self.results_callback.task_unreachable.items():
            result_raw['unreachable'][host] = result._result

        result_full = copy.deepcopy(result_raw)
        result_json = self.deal_result(result_raw)
        if not result_json['failed']:
            return result_json
        else:
            return result_full
        # return result_raw

    def run_playbook(self, file, **kwargs):
        if not os.path.isfile(file):
            raise Exception("%s file not found!" % file)
        try:
            # extra_vars = {}  # 额外的参数 sudoers.yml以及模板中的参数，它对应ansible-playbook test.yml --extra-vars "host='aa' name='cc' "
            self.variable_manager.extra_vars = kwargs

            playbook = PlaybookExecutor(playbooks=['' + file], inventory=self.inventory,
                                        variable_manager=self.variable_manager,
                                        loader=self.loader, options=self.options, passwords=self.passwords)

            playbook._tqm._stdout_callback = self.results_callback
            playbook.run()
        except Exception as e:
            print("error:", e.message)

        # 定义字典用于接收或者处理结果
        result_raw = {'success': {}, 'failed': {},
                      'unreachable': {}, 'skipped': {}, 'status': {}}

        # 循环打印这个结果，success，failed，unreachable需要每个都定义一个
        for host, result in self.results_callback.task_ok.items():
            result_raw['success'][host] = result._result
        for host, result in self.results_callback.task_failed.items():
            result_raw['failed'][host] = result._result
        for host, result in self.results_callback.task_unreachable.items():
            result_raw['unreachable'][host] = result._result

        # for host, result in self.results_callback.task_skipped.items():
        #     result_raw['skipped'][host] = result._result
        #
        # for host, result in self.results_callback.task_stats.items():
        #     result_raw['status'][host] = result._result

        result_full = copy.deepcopy(result_raw)
        result_json = self.deal_result(result_raw)
        if not result_json['failed']:
            return result_json
        else:
            return result_full


class AnsiInterface(AnsibleAPI):
    def __init__(self, hostfile, *args, **kwargs):
        super(AnsiInterface, self).__init__(hostfile, *args, **kwargs)

    def copy_file(self, src=None, dest=None):
        """
        copy file
        """
        module_args = "src=%s  dest=%s" % (src, dest)
        result = self.run('copy', module_args)
        return result

    def exec_command(self, cmds):
        """
        commands
        """
        result = self.run('command', cmds)
        return result

    def exec_script(self, path):
        """
        在远程主机执行shell命令或者.sh脚本
        """
        result = self.run('shell', path)
        return result
