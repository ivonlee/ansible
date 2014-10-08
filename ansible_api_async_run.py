import tornado.ioloop
from tornado.options import define, options
import tornado.web
import ansible.runner
from ansible.inventory import Inventory
import simplejson
import hashlib
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import sys
import time
from psutil import Process
import datetime
from threading import Thread

define("key", default='d41d8cd98f00b204e9800998ecf8427e')
mongoinfo = {"host": "127.0.0.1", "port": "27017", "user":
    "ops", "password": "ops", "dbname": "ansible_log"}
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

WORKER_TIMEOUT = 5 * 60
NUMBER_OF_TASK_PER_PAGE = 25
ANSIBLE_FORKS = 30
ANSIBLE_INVENTORY = '/etc/ansible/hosts'


def getmd5(str):
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()


def ConnMongoDB():
    global mongoinfo
    dbhost = mongoinfo['host']
    dbport = mongoinfo['port']
    dbuser = mongoinfo['user']
    dbpwd = mongoinfo['password']
    dbname = mongoinfo['dbname']
    uri = 'mongodb://%s:%s@%s/%s' % (dbuser, dbpwd, dbhost, dbname)
    return uri


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class CommandHandler(tornado.web.RequestHandler):
    def post(self):
        data = simplejson.loads(self.request.body) 
        badcmd = ['reboot','rm','kill','pkill','shutdown','half','mv','dd','mkfs','>','wget']

        type = data['type']
        cmd = data['cmd']
        host = data['host']
        print host
        sign = data['sign']
        isudo = data['sudo']
        cmdinfo = cmd.split(" ",1)
        print type,host,options.key
        hotkey = type+host+options.key
        print hotkey
        result = getmd5(hotkey)
        print result
        
        if sign != result:
            self.write("Sign is Error")
        else:
          if cmdinfo[0] in badcmd:
            self.write("This is Danger Shell")
          else:
            if "," in host:
               inventory = host.split(",")
               for host in inventory:
                   runner = ansible.runner.Runner(
                     module_name=type,
                     module_args=cmd,
                     pattern=host,
                     sudo = isudo,
                     forks=ANSIBLE_FORKS
                   )
                   result = runner.run()
                   now = datetime.datetime.now()
                   true = 'True'
                   result['time'] = now.strftime(TIME_FORMAT)
                   result['type'] = 'ad-hoc'
                   result['sudo'] = isudo
                   result['cmd'] = cmd
                   result['inventory'] = host
                   self.write(result)

                   uri = ConnMongoDB()
                   client = MongoClient(uri, safe=False)
                   db = client.ansible_log
                   db.ad_hoc.insert(result)
            else:
               runner = ansible.runner.Runner(
                     module_name=type,
                     module_args=cmd,
                     pattern=host,
                     sudo = isudo,
                     forks=ANSIBLE_FORKS
               )
               result = runner.run()
               now = datetime.datetime.now()
               true = 'True'
               result['time'] = now.strftime(TIME_FORMAT)
               result['type'] = 'ad-hoc'
               result['sudo'] = isudo
               result['cmd'] = cmd
               result['inventory'] = inventory
               self.write(result)

               uri = ConnMongoDB()
               client = MongoClient(uri, safe=False)
               db = client.ansible_log
               db.ad_hoc.insert(result)

class AsyncTaskHandler(tornado.web.RequestHandler):
    def post(self):
        data = simplejson.loads(self.request.body)
        badcmd = ['reboot', 'rm', 'kill', 'pkill',
                  'shutdown', 'half', 'mv', 'dd', 'mkfs', '>', 'wget']

        type = data['type']
        cmd = data['cmd']
        inventory = data['host']
        sign = data['sign']
        isudo = data['sudo']
        cmdinfo = cmd.split(" ", 1)
        print type, inventory, options.key
        hotkey = type + inventory + options.key
        print hotkey
        result = getmd5(hotkey)
        print result
        
        now = datetime.datetime.now()

        taskinfo = {}
        taskinfo['mode'] = type
        taskinfo['cmd'] = cmd
        taskinfo['inventory'] = inventory
        taskinfo['type'] = 'async ad-hoc'
        taskinfo['start'] = now.strftime(TIME_FORMAT)
        taskinfo['sudo'] = isudo
        
        uri = ConnMongoDB()
        client = MongoClient(uri, safe=False)
        db = client.ansible_log
        id=db.ansible_task.insert(taskinfo)
        mongoid={"_id":ObjectId(id)}
        print id

        if sign != result:
            self.write("Sign is Error")
        else:
            if cmdinfo[0] in badcmd:
                self.write("This is Danger Shell")
            else:
                runner = ansible.runner.Runner(
                    module_name=type,
                    module_args=cmd,
                    pattern=inventory,
                    sudo = isudo,
                    forks=ANSIBLE_FORKS
                )
                _, res = runner.run_async(time_limit = WORKER_TIMEOUT)
                now = time.time()
                while True:
                  if res.completed or time.time() - now > WORKER_TIMEOUT:
                      break
                  results = res.poll()
                  results = results.get('contacted')
                  if results:
                     for result in results.items():
                       jobinfo = {}
                       data = result[1]
                       print data
                       inventory = result[0]
                       jobinfo['inventory']=inventory
                       jobinfo['job_id']=data['ansible_job_id']
                       jobinfo['cmd']=data['cmd']
                       jobinfo['task_id']=id
                       uri = ConnMongoDB()
                       client = MongoClient(uri, safe=False)
                       db = client.ansible_log
                       id2 = db.ansible_job.insert(jobinfo)
                       mongoid2 = {"_id":ObjectId(id2)}
                       
                       if data['rc'] == 0 :
                         thisinfo2 = db.ansible_job.find_one(mongoid2)
                         thisinfo2['rc']=data['rc']
                         thisinfo2['stdout']=data['stdout']
                         thisinfo2['stderr']=data['stderr']
                         db.ansible_job.save(thisinfo2)
                         thisinfo = db.ansible_task.find_one(mongoid)
                         thisinfo['end'] = data['end'] 
                         thisinfo['rc'] = data['rc']
                         db.ansible_task.save(thisinfo)

                       elif data['rc'] == 1 :
                         thisinfo2 = db.ansible_job.find_one(mongoid2)
                         thisinfo2['rc']=data['rc']
                         thisinfo2['stderr']=data['stderr']
                         db.ansible_job.save(thisinfo2)
                         thisinfo = db.ansible_task.find_one(mongoid)
                         thisinfo['rc'] = data['rc']
                         db.ansible_task.save(thisinfo)

                       else:
                         thisinfo2 = db.ansible_job.find_one(mongoid2)
                         thisinfo2['rc']=data['rc']
                         thisinfo2['stderr']=data['msg']
                         db.ansible_job.save(thisinfo2)
                         thisinfo = db.ansible_task.find_one(mongoid)
                         thisinfo['rc'] = data['rc']
                         db.ansible_task.save(thisinfo)
 

                time.sleep(2)

class GetGroupHandler(tornado.web.RequestHandler):
    def get(self):
        i = Inventory()
        groups = i.list_groups()
        self.write('\n'.join(groups))

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/asynctask", AsyncTaskHandler),
    (r"/command", CommandHandler),
    (r"/getgroup", GetGroupHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
