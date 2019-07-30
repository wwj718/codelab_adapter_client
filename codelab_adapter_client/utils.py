import functools
import threading
import time


def threaded(function):
    """
    https://github.com/malwaredllc/byob/blob/master/byob/core/util.py#L514

    Decorator for making a function threaded
    `Required`
    :param function:    function/method to run in a thread
    """

    @functools.wraps(function)
    def _threaded(*args, **kwargs):
        t = threading.Thread(
            target=function, args=args, kwargs=kwargs, name=time.time())
        t.daemon = True  # exit with the parent thread
        t.start()
        return t

    return _threaded