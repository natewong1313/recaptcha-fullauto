from loguru import logger
import random
import time
import os

def sleep_random(min_time, max_time):
    delay = random.uniform(min_time, max_time)
    logger.debug(f"Sleeping for {delay} seconds")
    time.sleep(delay)

def load_proxy():
    with open(os.path.join(os.getcwd(), "proxies.txt"), "r") as file:
        lines = file.read().splitlines()
        if len(lines) == 0:
            raise Exception("No proxies found in proxies.txt")
        proxy_split = random.choice(lines).split(":")
        if len(proxy_split) == 2:
            return {
                "ip": proxy_split[0], 
                "port": int(proxy_split[1])
            }
        else:
            return {
                "ip": proxy_split[0], 
                "port": int(proxy_split[1]),
                "user": proxy_split[2], 
                "pass": proxy_split[3]
            }