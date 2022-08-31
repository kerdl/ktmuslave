import sys
import loguru

if __name__ == "__main__":
    sys.path.append(".")

    from src import defs
    defs.init_all()

    from svc import common
    common.run_forever()