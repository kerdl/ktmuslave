import sys
from loguru import logger

if __name__ == "__main__":
    #action = "convert"
    action = "add_to_redis"

    if action == "convert":
        sys.path.append(".")

        from src import defs
        defs.init_all()

        from svc import common
        common.run_forever()
    elif action == "add_to_redis":
        import redis
        from redis.commands.json.path import Path
        import json
        from json.encoder import JSONEncoder

        db = redis.Redis("192.168.1.127", 6379)

        with open("./data/ctx.json", mode="r", encoding="utf8") as f:
            str_ctxs = f.read()
            dict_ctxs: dict = json.loads(str_ctxs)

            for key, content in dict_ctxs.items():
                db.json(encoder=JSONEncoder(default=str)).set(key, Path.root_path(), content, decode_keys=True)