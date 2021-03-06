#!/usr/bin/python3

import requests
import tornado
import keys
import json
import redis
from sllog import DEBUG
from sllog import ERROR
import shunlu_config

APPID = "wx5bc95d4c482d0e1e"
SECRET = "54c56a02ab2ec18e3d21bf092b2b332a"
GRANT_TYPE = "authorization_code"

def getOpenId(code):
    # 微信官方示例: https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=JSCODE&grant_type=authorization_code
    request_params = {"appid": APPID, "secret": SECRET, "js_code": code, "grant_type": GRANT_TYPE}
    r = requests.get("https://api.weixin.qq.com/sns/jscode2session?", params = request_params)
    json_obj = json.loads(r.text)
    if "errcode" in json_obj:
        #sllog.writelog(ERROR, "get openid error with params: "+str(request_params))
        print("get openid error with params: " + str(request_params))
        return -1, "", ""
    return 1, json_obj["openid"], json_obj["session_key"]

#FIXME: update the login status of user in Redis
class LoginHandler(tornado.web.RequestHandler):

    def get(self):
        js_code = self.get_argument("jscode")
        iRet, openid, session_key = getOpenId(js_code)

        result = {}
        result["error_code"] = iRet
        result["openid"] = openid

        print("get a login request with openid="+str(openid))

        rds = redis.StrictRedis(shunlu_config.redis_ip, shunlu_config.redis_port)
        if not rds.exists("user"+openid): 
            rds.hmset("user"+openid, {"balance": 0, "user_name": "Test"})
        old_user_data = rds.hgetall("user"+openid)
        old_user_data["session_key"] = session_key
        rds.hmset("user"+openid, old_user_data)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(result))

