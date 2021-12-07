from datetime import datetime, timedelta


def older(path, **kwargs) -> bool:
    return datetime.fromtimestamp(path.stat().st_mtime) < (datetime.now() - timedelta(**kwargs))
