# coding=utf8

#  存储各项配置信息的redis
REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
    "password": "",
    "max_connections": 40,
    "socket_timeout": 1,
    "decode_responses": True
}

#  作为命中日志队列的redis
LOG_REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
    "password": "",
    "max_connections": 40,
    "socket_timeout": 1,
    "decode_responses": True
}

#  存储上报数据的redis
REPORT_REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
    "password": "",
    "max_connections": 40,
    "socket_timeout": 1,
    "decode_responses": True
}

# 存储命中日志的mysql
LOG_MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': 'root',
    'charset': 'utf8',
    'db': 'risk_control',
}

"""mongo数据目的地"""
SOC_MONGO_HOST = [
    "127.0.0.1:27017",
]


MONGO_DB = "risk_control"
