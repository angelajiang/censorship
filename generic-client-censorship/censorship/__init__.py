"""
Package template

Author: John Otto <jotto@eecs.northwestern.edu>
"""

# Only use integers separated by periods. 
# Don't use letters to indicate maturity
#   (e.g. a or b for alpha or beta).
__version__ = "1.0"

import logging
from Queue import Queue
from threading import Thread


_LOGGER = logging.getLogger(__name__)


_MAIN = None


class RunLoop(Thread):

    class ShutdownSignal: pass

    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.daemon = True

        self.q = Queue()

        # keep handle to top-level run script
        self.bootstrap = kwargs.get("bootstrap")

        self.interval = 3600

    def shutdown(self):
        self.q.put(RunLoop.ShutdownSignal())

    def run(self):
        while True:
            # add code here to run immediately
            try:
                command = self.q.get(timeout=self.interval)
            except QueueEmpty:
                # add code here to run periodically
                continue
            if isinstance(command, RunLoop.ShutdownSignal):
                break


def init(**kwargs):
    global _MAIN
    _MAIN = RunLoop(**kwargs)
    _MAIN.start()


def shutdown(block=True):
    if _MAIN and _MAIN.isAlive():
        _MAIN.shutdown()
    if block:
        _MAIN.join()
