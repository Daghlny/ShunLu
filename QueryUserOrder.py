#!/usr/bin/python3

import tornado.web
import redis
import json
import keys
import shunlu_config

charset = "utf-8"


class QueryUserOrdersService(object):
    def __init__(self):
        self.rds = redis.StrictRedis(shunlu_config.redis_ip, shunlu_config.redis_port)

    def getOrders(self, userid):
        useridInRedis = "user" + str(userid)
        # 用户不存在时的返回值, 待确定
        if not self.rds.exists(useridInRedis):
            return -1, [], [], [], []

        user_exist = 1
        finished_orders = list()
        canceled_orders = list()
        worker_orders = list()
        master_orders = list()

        worker_key = keys.worker_k_prefix + str(userid)
        master_key = keys.master_k_prefix + str(userid)
        finished_key = keys.finished_k_predix + str(userid)
        canceled_key = keys.canceled_k_prefix + str(userid)

        worker_orders_keys = self.rds.smembers(worker_key)
        master_orders_keys = self.rds.smembers(master_key)
        finished_orders_keys = self.rds.smembers(finished_key)
        canceled_orders_keys = self.rds.smembers(canceled_key)

        print("worker: ", end="")
        for key in worker_orders_keys:
            key = key.decode(charset)
            print(key+" ", end="")
            worker_orders.append(self.rds.get(key).decode(charset))
        print("|", end="")

        print("master: ", end="")
        for key in master_orders_keys:
            key = key.decode(charset)
            print(key+" ", end="")
            master_orders.append(self.rds.get(key).decode(charset))
        print("|", end="")

        print("finished: ", end="")
        for key in finished_orders_keys:
            key = key.decode(charset)
            print(key+" ", end="")
            finished_orders.append(self.rds.get(key).decode(charset))
        print("|", end="")

        print("canceled: ", end="")
        for key in canceled_orders_keys:
            key = key.decode(charset)
            print(key+" ", end="")
            canceled_orders.append(self.rds.get(key).decode(charset))
        print(" ")

        return 1, worker_orders, master_orders, finished_orders, canceled_orders


class QueryUserOrdersHandler(tornado.web.RequestHandler):
    service = QueryUserOrdersService()

    def get(self):
        userid = self.get_argument("user_id")
        print("get a request for user_orders with userid="+str(userid))
        
        user_exist, worker_str_array, master_str_array, finished_str_array, canceled_str_array = self.service.getOrders(userid)
        result = {}
        if user_exist < 0:
            result = {
                "my_worker_orders" : [""],
                "my_master_orders" : [""],
                "my_finished_orders" : [""],
                "my_canceled_orders" : [""],
            }
        else :
            worker_orders_array   = list()
            master_orders_array   = list()
            other_orders_array    = list()
            canceled_orders_array = list()
            for i in range(0, len(worker_str_array)):
                worker_orders_array.append(json.loads(worker_str_array[i]))
            for i in range(0, len(master_str_array)):
                master_orders_array.append(json.loads(master_str_array[i]))
            for i in range(0, len(finished_str_array)):
                other_orders_array.append(json.loads(finished_str_array[i]))
            for i in range(0, len(canceled_str_array)):
                canceled_orders_array.append(json.loads(canceled_str_array[i]))
            #result = "{\"my_worker_orders\": "+worker_orders_str+", " + "\"my_master_orders\": "+master_orders_str+", " + "\"other_orders\": "+other_orders_str+"}"
            result = {
                "my_worker_orders": worker_orders_array,
                "my_master_orders": master_orders_array,
                "my_finished_orders": other_orders_array,
                "my_canceled_orders": canceled_orders_array,
            }

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(result))

