ansible
=======
ansible-api.py 接受json格式数据post请求(部分是get请求)后通过ansible-api返回数据的tornado脚本


IP:PORT/command

模拟数据 
{"type":"command","cmd":"df  -h","host":"192.168.3.169","sign":"bc5361ff1562351c70ec74f68420eb3c"}


IP:PORT/getgroup （或者ansible host文件中组信息）

直接get即可



log_plays_inmongodb.py 是一个ansible callback插件，将ansible运行结果写入到mongodb


ansible_api_async_run.py 增加ansible异步执行功能


模拟数据

{"type":"command","cmd":"ping -c 15 www.baidu.com","host":"gmop-fs-3top7-3-*","sign":"2eb7e6e94dd8fd1652693308919fd7cf","sudo":"True"}
