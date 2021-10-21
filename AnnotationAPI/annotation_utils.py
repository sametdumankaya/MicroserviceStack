class AnnotationsUtils:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.blackhole_time_counter = 0
        self.portshutdown_time_counter = 0

    def get_redis_data(self, key):
        # result = self.redis_client.hgetall("poc_data")
        result = self.redis_client.xrevrange(key, "+", "-", 1)
        return result
