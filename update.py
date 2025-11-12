import time as _time
# attempt to detect host/VM clock offset and adjust Python's time() if needed.
try:
    import requests as _requests
    def _get_time_offset():
        try:
            r = _requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
            r.raise_for_status()
            data = r.json()
            # prefer 'unixtime' when available
            real = int(data.get("unixtime") or data.get("unixtime", 0))
            return real - int(_time.time())
        except Exception as _e:
            LOGGER.warning(f"Time offset fetch failed: {_e}")
            return 0

    _OFFSET = _get_time_offset()
    if abs(_OFFSET) > 2:
        LOGGER.info(f"🕒 Applying time offset: {_OFFSET}s to process time() to match UTC")
        _old_time = _time.time
        _time.time = lambda: _old_time() + _OFFSET
    else:
        LOGGER.info(f"🕒 Time offset small ({_OFFSET}s), no adjustment needed")
except Exception as _ex:
    LOGGER.warning(f"Time offset check skipped: {_ex}")
