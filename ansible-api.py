import tornado.ioloop
from tornado.options import define, options
import tornado.web
import ansible.runner
from ansible.inventory import Inventory
import simplejson
import hashlib

define("key", default='d41d8cd98f00b204e9800998ecf8427e')

def getmd5(str):
      m = hashlib.md5()   
      m.update(str)
      return m.hexdigest()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class CommandHandler(tornado.web.RequestHandler):
    def post(self):
        data = simplejson.loads(self.request.body) 
        badcmd = ['reboot','rm','kill','pkill','shutdown','half','mv','dd','mkfs','wget']

        type = data['type']
        cmd = data['cmd']
        host = data['host']
        sign = data['sign']
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
            runner = ansible.runner.Runner(
               module_name=type,
               module_args=cmd,
               pattern=host,
               forks=10
            )
            datastructure = runner.run()
            self.write(datastructure)

class GetGroupHandler(tornado.web.RequestHandler):
    def get(self):
      i = Inventory()
      groups = i.list_groups()
      self.write('\n'.join(groups))

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/command", CommandHandler),
    (r"/getgroup", GetGroupHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
