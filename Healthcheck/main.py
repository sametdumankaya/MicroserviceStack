from twilio.rest import Client
import requests
import shutil
import redis
import psutil


def send_sms(phone_numbers: list, message: str):
    account_sid = "AC5876e6a1dd275fbc8125ab69cb5175aa"
    auth_token = "1ff0cd5a783b67fef4b8833b3f61f138"
    client = Client(account_sid, auth_token)

    for phone in phone_numbers:
        client.messages.create(
            body=message,
            from_='+17605092801',
            to=phone
        )


def check_magifinance_website():
    try:
        requests.get("https://magifinance.com/")
        return "OK"
    except Exception as e:
        return "Cannot access magifinance.com. "


def check_disk_usage(free_disk_limit_gb: int):
    total, used, free = shutil.disk_usage("/")
    free = free // (2**30)
    return "OK" if free > free_disk_limit_gb else f"Free disk space is less than {free_disk_limit_gb} GB. "


def check_redis(redis_host: str, redis_port: int):
    try:
        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        redis_client.ping()
        keys_result = redis_client.keys("*")
        if len(keys_result) == 0:
            return "No data available on Redis. "
        return "OK"
    except redis.exceptions.ConnectionError as e:
        return "Cannot access Redis. "
    except:
        return "There is a problem with Redis. "


def check_memory_usage(free_memory_limit_percent: float):
    free_memory_percent = 100 - psutil.virtual_memory().percent
    if free_memory_percent < free_memory_limit_percent:
        return f"Free RAM space is less than {free_memory_limit_percent}%. "
    return "OK"


sms_message = ""
magifinance_result = check_magifinance_website()
disk_usage_result = check_disk_usage(free_disk_limit_gb=10)
memory_usage_result = check_memory_usage(free_memory_limit_percent=20)
redis_result = check_redis(redis_host="localhost", redis_port=6380)

if magifinance_result != "OK":
    sms_message += magifinance_result
if disk_usage_result != "OK":
    sms_message += disk_usage_result
if memory_usage_result != "OK":
    sms_message += memory_usage_result
if redis_result != "OK":
    sms_message += redis_result

if sms_message != "":
    send_sms(["+905379350275"], sms_message)

























