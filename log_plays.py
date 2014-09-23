import os
import time
import json
import datetime
from pymongo import MongoClient

mongoinfo = {"host":"127.0.0.1","port":"27017","user":"ops","password":"ops","dbname":"ansible_log"}  
TIME_FORMAT='%Y-%m-%d %H:%M:%S'

def InsertDB(values):
    global mongoinfo
    dbhost = mongoinfo['host']
    dbport = mongoinfo['port']
    dbuser = mongoinfo['user']
    dbpwd  = mongoinfo['password']
    dbname = mongoinfo['dbname']
    uri = 'mongodb://%s:%s@%s/%s'%(dbuser,dbpwd,dbhost,dbname)
    client = MongoClient(uri,safe=False)
    db = client.ansible_log
    db.callback.insert(values)    


class CallbackModule(object):
    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        now = datetime.datetime.now()
        result = res
        result['time'] = now.strftime(TIME_FORMAT)
        result['status'] = 'fail'
        InsertDB(result)
        
    def runner_on_ok(self, host, res):
        now = datetime.datetime.now()
        result = res
        result['time'] = now.strftime(TIME_FORMAT)
        result['status'] = 'ok'
        InsertDB(result)

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        now = datetime.datetime.now()
        result = res
        result['time'] = now.strftime(TIME_FORMAT)
        result['status'] = 'unreachable'
        InsertDB(result)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass
    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass
    def playbook_on_not_import_for_host(self, host, missing_file):
        pass
    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        pass
