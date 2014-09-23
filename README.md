ansible
=======
ansible-api.py 接受json格式数据post请求(部分是get请求)后通过ansible-api返回数据的tornado脚本


IP:PORT/command

模拟数据 
{"type":"command","cmd":"df  -h","host":"192.168.3.169","sign":"bc5361ff1562351c70ec74f68420eb3c"}


IP:PORT/getgroup （或者ansible host文件中组信息）

直接get即可



log_plays_inmongodb.py 是一个ansible callback插件，将ansible运行结果写入到mongodb
