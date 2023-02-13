import threading, queue, sys, time, logging

logger = logging.getLogger(__name__)

class WorkerThread:
    """!
    @brief A worker thread to post callables onto.
    @detail
    The thread is automatically destroyed after a second of inactivity, and recreated as necessary.
    """
    def __init__(self, onerror=None, timeout_s=None):
        """!
        @param[in] onerror	Called when a job fails with an exception.
        @param[in] timeout_s	Idle duration before the thread is shuttered (default 1).
        """
        self._onerror = None
        if timeout_s is None:
            self._timeout_s = 1
        else:
            self._timeout_s = timeout_s
        self._lock = threading.RLock()
        self._thread = None
        self._work_queue = queue.Queue() # sending None means to end the thread, anything else is a new job
        self._number_of_jobs_pending = 0

        # Passing a token object from one _WorkerThread to the next ensures that only one
        # _WorkerThread can run at a time.
        self._thread_ordering_queue = queue.Queue()
        self._thread_ordering_queue.put(None)

    def job(self, job):
        with self._lock:
            if self._work_queue is None:
                raise RuntimeError('closed')
            self._work_queue.put(job)
            if self._thread is None:
                self._thread = _WorkerThread(self)
                self._thread.start()
            self._number_of_jobs_pending += 1

    def peek_idle(self):
        """!
        @brief Check if the worker thread is idle.
        @return True if idle.
        @detail
        Subject to race conditions.
        """
        with self._lock:
            return self._number_of_jobs_pending == 0

    def close(self):
        """!
        @brief Shut down the worker thread and cease to accept new jobs.
        """
        with self._lock:
            q = self._work_queue
            if q is None:
                return
            self._work_queue = None
        q.put(None)

        
class _WorkerThread(threading.Thread):
    def __init__(self, owner):
        threading.Thread.__init__(self)
        self._owner = owner

    def run(self):
        owner = self._owner
        del self._owner

        # Ensure that the previous thread is done with its last job.
        owner._thread_ordering_queue.get()
        try:
            while 1:
                try:
                    job = owner._work_queue.get(block=True, timeout=owner._timeout_s)
                except queue.Empty:
                    with owner._lock:
                        # Repeat the test to avoid a race condition.
                        if owner._work_queue.empty():
                            owner._thread = None
                            return
                        else:
                            continue

                if job is None:
                    break
                try:
                    job()
                except:
                    if owner._onerror is not None:
                        owner._onerror(sys.exc_info())
                    else:
                        logger.error("Background task failed", exc_info=sys.exc_info())
                job = None
                with owner._lock:
                    owner._number_of_jobs_pending -= 1
                
        finally:
            owner._thread_ordering_queue.put(None) # hand over to the next thread
