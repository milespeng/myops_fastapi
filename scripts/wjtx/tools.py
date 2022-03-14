import time
from scripts.common.ansible import AnsiInterface, write_host
import redis
from scripts.common.mmysql import MysqlBase
import json
from scripts.logger import logger as log

config = {
    "global_redis_conf": {
        "host": "10.10.6.4",
        "port": "6379"
    },
    "game_conf": {
        "host": "10.10.6.2",
        "port": 3306,
        "user": "wjtx",
        "pswd": "mMWA4DKCfeOL"
    }
}


class WjtxTools:
    def __init__(self) -> None:
        self.mysql_conf = config['game_conf']
        self.redis_conf = config['global_redis_conf']

    async def change_start_time(self, serverid: int, start_time: str) -> bool:
        self.serverid = serverid
        self.mysql_conf['db'] = f"legend_{self.serverid}"
        if self.check_serverid():
            if self._change_db(start_time):
                if self._restart_service():
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def _reset_worldboss(self, values):
        legend_db = MysqlBase(**self.mysql_conf)
        tablename = "world_boss"
        u_data = {'worldboss_level': values}
        try:
            legend_db.update(tablename, u_data, True)
            log.info(f"change world_boss to {values} success!")
            return True
        except Exception as e:
            log.error(e)
            return False

    # def _restart_stage(self):
    #     global_redis = redis.Redis(host=self.redis_conf['host'], port=self.redis_conf['port'], charset='utf8',
    #                                db=self.redis_conf.get('db') or 0)
    #     host_info = json.loads(global_redis.hget('game_info', self.serverid))
    #     hostip = host_info.get('innerIp', None)
    #     if not hostip:
    #         log.error(f"get host with {self.serverid} failed ,{host_info}")
    #         return False

    #     restart_cmd = f"su - kingsome -c 'cd /data/apps/game1009stage && sh restart.sh {self.serverid}'"
    #     hostfilename = write_host(hostip)
    #     time.sleep(1)
    #     myansible = AnsiInterface(hostfilename)
    #     resule = myansible.exec_command(restart_cmd)
    #     log.debug(resule)
    #     if not (resule['failed'] or resule['unreachable']):
    #         log.info(f"restart {self.serverid} success!")
    #         return True
    #     else:
    #         log.error(f"restart {self.serverid} failed,output was {resule}")
    #         return False

    def _change_db(self, opentime):
        legend_db = MysqlBase(**self.mysql_conf)
        # update server_info set start_time='2020-03-16 11:00:00';
        tablename = "server_info"
        u_data = {'start_time': opentime}
        try:
            legend_db.update(tablename, u_data, True)
            log.info("change db success!")
            return True
        except Exception as e:
            log.error(e)
            return False

    def _restart_service(self):
        global_redis = redis.Redis(host=self.redis_conf['host'],
                                   port=self.redis_conf['port'],
                                   charset='utf8',
                                   db=self.redis_conf.get('db') or 0)
        host_info = json.loads(global_redis.hget('game_info', self.serverid))
        hostip = host_info.get('innerIp', None)
        if not hostip:
            log.error(f"get host info with {self.serverid} failed!")
        if int(self.serverid) < 20000:
            restart_cmd = f"su - kingsome -c 'cd /data/apps/game1009game && sh restart.sh {self.serverid}'"
        else:
            restart_cmd = f"su - kingsome -c 'cd /data/apps/game1012game && sh restart.sh {self.serverid}'"
        hostfilename = write_host(hostip)
        time.sleep(1)
        myansible = AnsiInterface(hostfilename)
        resule = myansible.exec_command(restart_cmd)
        log.debug(resule)
        if not (resule['failed'] or resule['unreachable']):
            log.info(f"restart {self.serverid} success!")
            return True
        else:
            log.error(f"restart {self.serverid} failed,output was {resule}")
            return False

    def check_serverid(self):
        global_redis = redis.Redis(host=self.redis_conf['host'],
                                   port=self.redis_conf['port'],
                                   charset='utf8',
                                   db=self.redis_conf.get('db') or 0)
        server_state = global_redis.hget('server_state', self.serverid)
        if int(server_state) != 12:
            return False
        else:
            log.info(f"{self.serverid} check ok!")
            return True

    async def change_worldboss(self, serverid: int, values: int) -> bool:
        self.serverid = serverid
        self.mysql_conf['db'] = f"legend_{self.serverid}"
        if self._reset_worldboss(values):
            if self._restart_stage():
                return True
            else:
                return False
        else:
            return False

    async def _get_alive_host(self) -> list:
        alive_serverids = list()
        global_redis = redis.Redis(host=self.redis_conf['host'],
                                   port=self.redis_conf['port'],
                                   charset='utf8',
                                   db=self.redis_conf.get('db') or 0)

        data = global_redis.hgetall('game_info')
        for line in data.values():
            recode = json.loads(line)
            # all_serverids.append(recode['areaId'])
            if (int(recode['areaId']) % 100 + 9000) == int(
                    recode['tcpPort']) and recode['status'] == 1:
                alive_serverids.append(recode['areaId'])
        all_serverids = list(set(alive_serverids))
        return all_serverids.sort()

    def _get_hostip_via_serverid(self, serverids) -> list:
        global_redis = redis.Redis(host=self.redis_conf['host'],
                                   port=self.redis_conf['port'],
                                   charset='utf8',
                                   db=self.redis_conf.get('db') or 0)
        all_hosts = list()
        for serverid in serverids:
            hostip = json.loads(global_redis.hget('game_info', serverid)).get(
                'innerIp', None)
            if hostip:
                all_hosts.append(hostip)
        return all_hosts

    async def stop_service(self, serverids: list) -> bool:
        if not serverids:
            all_services = await self._get_alive_host()
        else:
            all_services = serverids
        hosts = self._get_hostip_via_serverid(all_services)
        hostfilename = write_host(hosts)
        stop_cmd = "/usr/bin/pkill java"
        time.sleep(1)
        myansible = AnsiInterface(hostfilename)
        resule = myansible.exec_command(stop_cmd)
        log.debug(resule)
        if not (resule['failed'] or resule['unreachable']):
            log.info(f"stop {self.serverid} success!")
            return True
        else:
            log.error(f"stop {self.serverid} failed,output was {resule}")
            return False
