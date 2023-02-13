import sys
sys.path.insert(0, '..')
import time, unittest, threading
from wxdo import workerthread


class Test_WorkerThread(unittest.TestCase):
    def test_example(self):
        try:
            self._test_example(dT=0.01)
        except:
            try:
                self._test_example(dT=0.1)
            except:
                self._test_example(dT=1.0)
    def _test_example(self, dT):
        events = []
        lock = threading.Lock()
        def log(event):
            with lock:
                events.append(event)
        def mk_job(name, t):
            def job():
                log("<%s>" % (name,))
                sle(t)
                log("</%s>" % (name,))
            return job
        def sle(t):
            time.sleep(t * dT)
        w = workerthread.WorkerThread(timeout_s=dT)
        w.job(mk_job('a', 1))
        sle(2.5)
        w.job(mk_job('b', 0.5))
        sle(0.5)
        w.job(mk_job('c', 1))
        sle(1.5)
        w.job(mk_job('d', 1))
        sle(2.5)
        w.job(mk_job('e', 1))
        w.job(mk_job('f', 1))
        sle(5)
        w.job(mk_job('g', 1))
        sle(1.5)

        with lock:
            ev = events.copy()
        self.assertEqual(
            ev,
            [
            '<a>',
             '</a>',
             '<b>',
             '</b>',
             '<c>',
             '</c>',
             '<d>',
             '</d>',
             '<e>',
             '</e>',
             '<f>',
             '</f>',
             '<g>',
             '</g>',
             ]
            )


if __name__=='__main__':
    unittest.main()