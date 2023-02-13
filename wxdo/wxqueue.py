import wx.lib.newevent, queue, weakref

QueueEvent, EVT_QUEUE = wx.lib.newevent.NewEvent()

try:
    PyDeadObjectError = wx.PyDeadObjectError # pre-Phoenix
except AttributeError:
    PyDeadObjectError = RuntimeError # Phoenix

class WxQueue(queue.Queue):
    """WxQueue: Subclass of Queue.Queue for communicating values to a
    wx event handler.  Inserting an item into this Queue sends a
    message to a wxEventHandler, triggering an on-item callback.
    """
    def __init__(self, wxevthandler, onreceiveitem, maxsize=0):
        """wxevthandler: The wx.Window (or other wx.EvtHandler subclass)
               object that is to receive queue events.
         onreceiveitem: Queue receive callback. A callable taking a
               two arguments, wxevthandler and the item put into the queue.
        """
        queue.Queue.__init__(self, maxsize)
        self.__unhandled = False
        self.__onreceiveitem = None
        self.__wxevthandler_wr = lambda:None
        if wxevthandler is not None:
            assert onreceiveitem is not None
            self.BindReceiveItem(wxevthandler, onreceiveitem)
        else:
            assert onreceiveitem is None
            self.Unbind()

    def put(self, item, block=True, timeout=None):
        queue.Queue.put(self, item, block, timeout)
        self.__notify()

    def put_nowait(self, item):
        queue.Queue.put_nowait(self, item)
        self.__notify()

    def __OnEvtQueue(self, event):
        self.__unhandled = False
        wxevthandler = self.__wxevthandler_wr()
        while 1:
            try:
                next = self.get_nowait()
            except queue.Empty:
                break
            else:
                if self.__onreceiveitem is not None:
                    self.__onreceiveitem(wxevthandler, next)

    def BindReceiveItem(self, wxevthandler, onreceiveitem):
        try:
            assert not wxevthandler.__has_WxQueue, 'Each wxWindow can have only one WxQueue'
        except AttributeError:
            pass
        wxevthandler.__has_WxQueue = True
        self.__wxevthandler_wr = weakref.ref(wxevthandler)
        self.__onreceiveitem = onreceiveitem
        wxevthandler.Bind(EVT_QUEUE, self.__OnEvtQueue)

    def Unbind(self):
        wxevthandler = self.__wxevthandler_wr()
        if wxevthandler is not None:
            wxevthandler.Unbind(EVT_QUEUE)
            wxevthandler.__has_WxQueue = False
        self.__onreceiveitem = None
        self.__wxevthandler_wr = lambda:None

    def __notify(self):
        wxevthandler = self.__wxevthandler_wr()
        if wxevthandler is not None:
            if not self.__unhandled:
                self.__unhandled = True
                try:
                    wx.PostEvent(wxevthandler, QueueEvent())
                except PyDeadObjectError:
                    pass
