import types, sys, functools
from . import wxqueue, workerthread


class _TaskFunction:
    def __init__(self, coroutine_function):
        self._coroutine_function = coroutine_function

    def call(self, wxobj, *args, **kwargs):
        """!
        @brief Invoke the long-running task.
        @param[in] wxobj	wx.EventHandler, akin to 'self' in a normal event handler.
        """
        evh = _TaskInProgress(self, wxobj, *args, **kwargs)
        evh.foreground_continuation()


def task(coroutine_function):
    """!
    @brief Decorator to create long-running tasks from async methods.
    @param[in] coroutine_function	An 'async def' method.
    @return Wrapped to act like a regular method.
    @detail
    The returned function looks from the caller's perspective just like a regular method, one which
    wx events can be bound to.  But within the method, 'await aslong.switch_bg()' and related can be
    used, allowing the function to do work on a background thread instead of block the UI.
    """
    tf = _TaskFunction(coroutine_function)
    # Can't return evh.call directly, because an bound method will not be bound again, when appearing
    # in the class dict.
    @functools.wraps(coroutine_function)
    def call(wxobj, *args, **kwargs):
        return tf.call(wxobj, *args, **kwargs)
    return call

class TaskInterruptedError(InterruptedError): pass


class _TaskInProgress:
    def __init__(self, task, wxobj, *args, **kwargs):
        self._task = task
        self._wxobj = wxobj
        self._wxq, self._worker,self._inbackground = self._get_worker(wxobj)
        self._coroutine = task._coroutine_function(wxobj, *args, **kwargs)
        self._reply = None
        self._exc_info = None
        self._shutting_down = False # only accessed from foreground thread

    def _get_worker(self, wxobj):
        # Current implementation shares a worker thread among all event handlers on the same wx.Window.
        # One might change this to store something on self._task that says what
        # to do instead. E.g. using a shared thread from a global pool, or using a unique thread for
        # the particular _TaskFunction. (With still only one WxQueue, might be doable.)
        #
        # inbackground is the set of _TaskInProgress for which an item might potentially appear in wxq,
        # the queue of jobs returned from the background thread to the foreground thread.
        # (It is entirely managed from the foreground side, and so needs no locks.)
        try:
            wxq,worker,inbackground = wxobj.__aslong_backend
        except AttributeError:
            wxq = wxqueue.WxQueue(wxobj, _invoke_foreground_continuation)
            worker = workerthread.WorkerThread()
            inbackground = set() # set of _TaskInProgress
            wxobj.__aslong_backend = wxq,worker,inbackground
        return wxq,worker,inbackground

    def foreground_continuation(self):
        self._inbackground.discard(self)
        if self._shutting_down:
            return self._shutdown_foreground_continuation()
        else:
            reply = self._reply
            while 1:
                try:
                    request = self._coroutine.send(reply)
                except StopIteration:
                    break

                if request == 'bg':
                    self._reply = None
                    self._inbackground.add(self)
                    self._worker.job(self.background_continuation)
                    break
                elif request == 'ui':
                    reply = None
                elif request == '?':
                    reply = True
                else:
                    raise NotImplementedError(repr(request))

    def background_continuation(self):
        reply = self._reply
        while 1:
            try:
                request = self._coroutine.send(reply)
            except StopIteration:
                self._wxq.put(self.finished_continuation)
                break
            except:
                self._exc_info = sys.exc_info()
                self._wxq.put(self.exception_continuation)
                break
            if request == 'ui':
                self._reply = None
                self._wxq.put(self.foreground_continuation)
                break
            elif request == 'bg':
                reply = None
            elif request == '?':
                reply = False
            else:
                raise NotImplementedError(repr(request))

    def exception_continuation(self):
        self._inbackground.discard(self)
        _exc_cls, exc, tb = self._exc_info
        raise exc.with_traceback(tb)

    def finished_continuation(self):
        self._inbackground.discard(self)
    
    def _set_as_shutting_down(self):
        self._shutting_down = True
                
    def _shutdown_foreground_continuation(self):
        inject_exception = TaskInterruptedError("destroying wx object '%s'" % (self._wxobj.Name,))
        reply = self._reply
        while 1:
            try:
                if reply is None:
                    request = self._coroutine.throw(inject_exception)
                else:
                    request = self._coroutine.send(reply)
            except (StopIteration, TaskInterruptedError):
                break
            else:
                if request == '?':
                    reply = True
                else:
                    reply = None

def _invoke_foreground_continuation(wxevthandler, foreground_continuation_bound_method):
    foreground_continuation_bound_method()

def cleanup(wxobj):
    """!
    @brief 
    """
    try:
        wxq,worker,inbackground = wxobj._TaskInProgress__aslong_backend
    except AttributeError:
        pass
    else:
        # Decouple the event that executes foreground work, and instead, pull the remaining
        # continuations, posted by the background tasks, directly from the queue.Queue interface.
        wxq.Unbind() # decouple
        for eip in inbackground:
            eip._set_as_shutting_down()
        while len(inbackground) > 0:
            continuation = wxq.get() # queue.Queue.get
            continuation()


def busy(wxobj):
    """!
    @brief Check for background tasks in progress.
    @param[in] wxobj	The wx.EvtHandler that the tasks are associated with.
    @return True if busy.
    @detail
    If called from a task in ui mode, the callee does not count as busy.
    """
    try:
        wxq,worker,inbackground = wxobj._TaskInProgress__aslong_backend
    except AttributeError:
        return False
    else:
        return len(inbackground) > 0


async def is_ui():
    """!
    @brief Check if on the wxPython GUI thread.
    @return True after switch_ui and during cleanup completion.
    """
    return await _event_loop('?')


@types.coroutine
def _event_loop(arg):
    # Interact with the event loop from user code.
    return (yield arg)


class bg:
    """!
    @brief Teleport the calling code to the background thread.
    @detail
    Use 'await bg()' to perform a teleport.
    Use 'async with bg:' to switch temporarily, then switch back.  ('cleanup' may be necessary.)
    """
    async def __call__(self):
        await _event_loop('bg')
    async def __aenter__(self):
        self._was_ui = await is_ui()
        await _event_loop('bg')
    async def __aexit__(self, exc_type, exc, tb):
        if self._was_ui:
            await _event_loop('ui')
bg = bg()

class ui:
    """!
    @brief Teleport the calling code to the wxPython GUI thread.
    @detail
    Use 'await ui()' to perform a teleport.
    Use 'async with ui:' to teleport temporarily, then teleport back.  ('cleanup' may be necessary.)
    """
    async def __call__(self):
        await _event_loop('ui')
    async def __aenter__(self):
        self._was_ui = await is_ui()
        await _event_loop('ui')

    async def __aexit__(self, exc_type, exc, tb):
        if not self._was_ui:
            await _event_loop('bg')
ui = ui()
