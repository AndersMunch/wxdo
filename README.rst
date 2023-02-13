wxdo
====

A collection of wxPython components and utilities.

* ``wxdo.aslong``: A system for delegating long-running tasks to a background thread.
* ``wxdo.deep_object_list``: A widget for editing a list of arbitrary content.
* ``wxdo.wxqueue``: A ``queue.Queue`` variant for sending work from a worker thread to the GUI thread.
* ``wxdo.sizers``: Sizer utilities.
* ``wxdo.workerthread``: Background worker thread manager.

Installation
============

``$ pip install wxdo``

Source code: https://github.com/AndersMunch/wxdo

  
aslong
======

*aslong* is for creating wxPython event handlers that are long-running, yet
don't block the user interface.

It uses *async* to achieve this, but not *asyncio*.  That means event handlers
can use ordinary blocking code, like ``time.sleep(...)``, ``requests.get(anURL)``,
```databasecursor.execute('SELECT ...')`` and such, and not their asyncio equivalents.

Event handlers are written as coroutine functions decorated with the
``aslong.task`` decorator.  Other than that they look just like regular event
handler methods, and as far as the body of the function is just regular event
handling code, nothing special happens.

Then you call ``await aslong.bg()``, and from that point on, the code is no
longer running in the UI thread. It has been teleported to a background thread,
and the UI is once again responsive, even though the event handler is still
running.

While on the background thread, time consuming work can be done, without
affecting the UI.

Then you call ``await aslong.ui()``, and from that point on, the code is no
longer running in the background thread. It has been teleported back to the UI
thread, and the results of the long-running work can be entered into the
wxPython GUI components.

Is is also possible to use ``aslong.ui`` and ``aslong.bg`` as async context managers.
Writing

.. code-block:: python

    async with aslong.bg:
        modify_ui()

is roughly equivalent to writing

.. code-block:: python

     await aslong.ui()
     try:
         modify_ui()
     finally:
         await aslong.bg()


The associated wx object
------------------------

The long-running task is associated with the object for which the event handler
is defined.

That is to say, e.g. if `self` is a panel, and you write:

.. code-block:: python

   def __init__(self):
       but = wx.Button(self, -1, "Press me")
       but.Bind(wx.EVT_BUTTON, self.OnButton)
   @aslong.task
   async def OnButton(self, event):
       ...

then a background worker thread is created (when necessary) for `self`, the
panel (not for the button), when the event handler is called.  All event
handlers on the same panel share the same thread.  You can start multiple
long-running tasks: If an event with a long-running task is triggered while
another long-running task is still running, then they take turns running their
background code, so that only one tasks background code is running at any time.

Background code can run concurrently, though: The background code with one
associated wx object runs concurrently with the background code for a different
associated wx object, as they each have their own background worker thread.


Cleanup
-------
When a wxPython object with associated long-running tasks is destroyed, any
tasks that are still running in the background are left hanging.

If they don't use any context managers and don't use any try..finally, then they
will just quitely stop when the current section of background work is done.  If
they do, then Python will complain with a mysterious error: ``RuntimeError:
coroutine ignored GeneratorExit``.  That's Python saying that there was some
cleanup work left to do, and it didn't get done, because a coroutine was
abandoned early.

To avoid abandoning coroutines, use ``aslong.cleanup(self)`` in the close or
destroy event of the associated wx object, to run still-running tasks to
completion.  Termination is done by ``await aslong.ui()`` raising an
``InterruptedError`` exception.  ``finally`` sections and context manager exits
will then be executed as part of normal stack unwinding.

During cleanup, all code is run on the UI thread (the thread that you called
``aslong.cleanup`` from).

See the sample ``aslong_multi.py`` for how to call ``cleanup``.

While the injected ``InterruptError`` speeds up the cleanup, it does mean that
the long-running work that was in progress is not finished.

You may opt to trap the InterruptedError exception in the event handler, and
so insist that the rest of the work is done. E.g. something like this:

.. code-block:: python

    for thing in many_things:
        try:
            await aslong.ui()
        except InterruptedError:
            pass # I won't be interrupted!
        else:
            self.label.SetValue("Still working")
        await aslong.bg()
        process(thing)

Just understand that the UI will then block until it's all done.  And keep in
mind that if the wxPython panel/frame/whatever is in the process of being
destroyed, then calling methods on that may fail.


Caveats and limitations 
-----------------------

Close and destroy events cannot be *aslong* long-running tasks.

When running on the background thread, the usual wxPython restrictions on
threaded code applies: Code on a background thread must not interact with
wxPython components.

More so, the wx.Event object that was passed to an event handler must only be
used in the initial part of the event handler, before the first visit to the
background thread.  After that, the C++ event object may have been destroyed.

All event handlers associated with the same wxPython object use the same
background worker thread, and background jobs are run sequentially on that
thread.  That gives you a little bit of thread-safety, but not a lot: Other
event handlers on other wxPython objects have their own thread that runs
independently.  Background code should use locks, ``threading.Lock`` and
``threading.RLock``, to safeguard shared resources, just like any other threaded
code.  UI code, on the other hand, never runs concurrently with other UI code --
there is only ever one UI thread, but you may still need to use locks, if
they're touching anything that a background thread for a different task may also
touch.

It is safe to hold a ``threading.Lock`` lock while teleporting between UI and
background, but do not teleport while holding a ``threading.RLock``.  Your task
may deadlock against itself, or worse.

If locks are held, then running ``aslong.cleanup()`` is important: Without it,
event handlers are not guaranteed to run to completion, which means that locks
may be held that are never released, causing deadlocks.

If any libraries are in use that are somehow tied to a specific thread, like
Windows COM objects, then *aslong* long-running tasks should not be used, unless
the thread is question is the GUI thread.  Although there is only one background
thread at any time, an idle background thread is eventually closed, and a new,
different, thread is created on demand.


DeepObjectList
==============

This is a wxPython list editing widget, where the list elements can be anything
that can be placed into a sizer - windows and complex sizers hierarchies alike.

List items can be added, deleted and reordered.

Lists can be heterogenous, i.e. list items in the same list can use different
controls and look very different from one another.

Creating a list uses three objects:

* A ``DeepObjectList``: The list control itself, which is a wx.Panel subclass.
* An object of a ``DeepObjectList_Parameters`` subclass, which configures what the list looks like.
* An object of a ``DeepObjectItemEditor`` subclass, which configures what a single list element looks like.

Getting started
---------------

First, make a DeepObjectList_Parameters subclass, and implement two key methods:
CreateObject and CreateItemEditor.

CreateObject creates a new value of the type you're editing a list of.  The
returned value can be any type of Python object: a number, a list, a
datetime.datetime, a pathlib.Path, or your own class that you just wrote,
whatever you like.

The second method, ``CreateItemEditor``, returns a ``DeepObjectItemEditor`` which 
in turn creates the wxPython controls needed to display and edit the value.

So if for example you are editing a list of strings, ``CreateObject`` could simply
return an empty string.  Let's make a slightly more complicated example: A list
of enumeration values that uses a ``wx.Choice`` to edit the values.

.. code-block:: python

    from enum import Enum, auto
    import wx
    from wxdo.deep_object_list import DeepObjectList, DeepObjectList_Parameters, DeepObjectItemEditor
    
    class Colour(Enum):
       unknown = auto()
       red = auto()
       green = auto()
       blue = auto()
    
    class Parameters(DeepObjectList_Parameters):
       def CreateObject(self, parent):
           return Colour.unknown
    
       def CreateItemEditor(self, value):
           return Colour_ItemEditor()
    

The value parameter to ``CreateItemEditor`` is the value of the list item to be
edited, allowing you to create different editors for different types of values.
In this case, there's only one type of value, so it isn't used.

The next step is the editor object.  It needs to implement ``Create`` and ``Destroy``
methods, to create and destroy wxPython controls, and ``SetValue``/``GetValue`` methods,
to set and get a list item value.


.. code-block:: python

    class Colour_ItemEditor(DeepObjectItemEditor):
        def Create(self):
            # self.parent is the appropriate parent to use for wxPython windows.
            self._choice = wx.Choice(self.parent, -1, choices=list(Colour.__members__.keys()))
            # Return a list of somethings that can be added to a sizer.
            return [self._choice]
    
        def SetValue(self, value):
           position = list(Colour.__members__.values()).index(value)
           self._choice.SetSelection(position)
    
        def GetValue(self):
           position = self._choice.GetSelection()
           return list(Colour.__members__.values())[position]
    
        def Destroy(self):
            self._choice.Destroy()


There are additional methods that can be overriden to fine-tune the behaviour of
the list.  See the ``DeepObjectList_Parameters`` class in the code.

Finally, put the whole thing together:

.. code-block:: python

    params = Parameters()
    the_list = DeepObjectList(parent, -1, params)
    some_sizer.Add(the_list, 1, wx.EXPAND)
    # the_list.GetValue() and the_list.SetValue() are ready to use.


Operating the list
------------------
The list supports reordering: Click on a hand icon and drag it on top of a
different hand icon, and then the list item is moved up or down to that
position.  This can also be done using the keyboard: press space or return on
the hand icon, or click without dragging, and then the icon changes to arrows
and the up/down arrow keys can then be used to move the list item.

The green [+] icon adds a new list item just before this one. There is a lone [+] icon
at the bottom to append to the list.

The red [x] icon deletes the list item.  By default it does not ask for
confirmation, but you can override ``DeepObjectList_Parameters.ConfirmErase`` to
change that.



The DeepObjectList class
------------------------

================== ==============================================================
Methods            
================== ==============================================================
SetValue           Set a list of Python objects as the value of the list widget.
GetValue           Get the value of the list widget as a list of Python objects.
SetLayoutCallback  Set a callback for when content changes size, and the full
                   list needs to be re-layouted.
SetTexts           Customise user interface texts.
GetItemEditors     Peek at the which DeepObjectItemEditor's are currently on-screen.
================== ==============================================================

Do not inherit from this class, use as is.  Adaptation takes place in a
``DeepObjectList_Parameters`` subclass.


The DeepObjectList_Parameters class
-----------------------------------

Make a subclass and implement ``CreateObject`` and ``CreateItemEditor`` methods.
The rest of the methods are optional, override as necessary.

================== ==============================================================
Methods            
================== ==============================================================
CreateObject       Called when the user pressed [+] to add an item.
ConfirmErase       Called to confirm when the user pressed [-] to delete an item.
CreateItemEditor   Create an item editor - an instance of a DeepObjectItemEditor subclass - to handle a list item.
GetColumnTitles    Override to add column titles.
GetEraseAllowed    To remove the destroy buttons, override to return False.
GetAddAllowed      To remove the add [+] buttons, override to return False.
GetReorderAllowed  To disable moving items up and down, override to return False.
================== ==============================================================

For each ``DeepObjectList`` there is exactly one ``DeepObjectList_Parameters``
to configure it.  However, there can be more than one item editor type: Each
list item being edited gets its own ``DeepObjectItemEditor`` object, and they
can be of different types to support a list with different kinds of elements.

The `recursive.py` example file demonstrates how.

Variable-sized item editors
---------------------------

Height resizing
+++++++++++++++
An item editor doesn't have to be fixed size.  It is possible to use controls
that change size, like e.g. a ``wx.lib.expando.ExpandoTextCtrl``.

For this to work, the list has to be notified when the height changes.  This is
done by calling ``DeepObjectItemEditor.LayoutCallback``.  Or alternatively, by
intercepting ``DeepObjectItemEditor.SetLayoutCallback``, as is done in the
``recurse.py`` sample.

Expanding to the available width
++++++++++++++++++++++++++++++++
Controls are by default added with the ``flag=wx.ALL`` sizer option, but not
``wx.EXPAND``.

To use controls that expand to use the available width, override the Add
parameters by returning a dict of Add parameters instead of a control from
``DeepObjectItemEditor.Create``.

That is, instead of returning a simple control like this:

.. code-block:: python

    def Create(self):
        self.edit = wx.TextCtrl(self.parent, -1)
        return [self.edit]

return a dict with an override value for ``flag``:

.. code-block:: python

    def Create(self):
        self.edit = wx.TextCtrl(self.parent, -1)
        return [dict(window=self.edit, flag=wx.ALL|wx.EXPAND)]

Embedding a list in a resizable context
+++++++++++++++++++++++++++++++++++++++
If you don't want the ``DeepObjectList`` to take up space when it contains few
or no items, then you may want to re-layout the panel or frame that it's on when
item are added to or removed from the list.

``DeepObjectList.SetLayoutCallback`` achieves this. When the vertical space needed for this list changes,
then it will call a callback set with ``DeepObjectList.SetLayoutCallback``.

This can be as simple as using the top-level window's ``wx.Window.Layout`` method:

.. code-block:: python

    aDeepObjectList.SetLayoutCallback(myFrame.Layout)


The DeepObjectItemEditor class
------------------------------

Make a new subclass of ``DeepObjectItemEditor`` and implement these methods.

================== ==============================================================
Methods            
================== ==============================================================
Create             Create wxPython components for editing an item.
Destroy            Destroy the wxPython components created by ``Create``.
SetValue           Set the value of being edited.
GetValue           Read back the edited value.
SetLayoutCallback  Provides a callable for the editor to use when changing size.
NotifyPosition     Called when the list position has changed.
================== ==============================================================

``Create`` returns a list of things to ``.Add`` to a sizer. That can be a single
``wx.Window`` or that can be the ``wx.Sizer`` at the root of sizer hierarchy.
Often the list only contains a single element. If multiple elements are
returned, then they become columns of the list.  The elements are placed in
```wx.GridBagSizer`` columns, so that columns from different item editors line up.

``SetLayoutCallback`` is only required if the wx control changes size during
editing.  If it does, it should callback the callback passed to it using
``SetLayoutCallback`` after the size has changed, to let outer layers know that a
``Layout`` may be necessary to adjust the positions of other controls around it.

Implement ``NotifyPosition`` to be informed of what position in the list the editor's at.
This is useful for changing the appearance to match the background colour for the position.
Takes two parameters ``index``, a 0-based index, and ``bgcol``, the background
colour. Remember that the background colour alternates for even and odd indexes,
so when the editor is moved up or down the list, the background colour should
change to match.


wxdo.wxqueue
============

The ``WxQueue`` class is a ``queue.Queue`` subclass designed for sending data
from a worker thread to a function that can change the GUI state accordingly. 

The queue is associated with a ``wx.Window``.  Work items can put into the queue
from any arbitrary thread. In the GUI thread the items are then popped one by
one, and an handler function is called with the item.  This handler function can
then update the GUI, since it's running on the GUI thread.

WxQueue(wxevthandler, onreceiveitem, maxsize=0)
-----------------------------------------------

WxQueue.__init__ takes three parameters

 * wxevthandler: The ``wx.Window`` that the queue is anchored to. Only one
   ``WxQueue`` can be anchored to any window.
 * onreceiveitem: A callback function that takes two parameters: The
   ``wx.Window`` and the next item popped from the queue.  Runs on the GUI
   thread.
 * maxsize: Parameter for ``queue.Queue.__init__``. 0 means unbounded queue.

Pushing to the queue
--------------------

Use the ``put`` and ``put_nowait`` methods, as described in the ``queue.Queue`` documentation.

Popping from the queue
----------------------

There's no need to pop manually from the queue. Just let the ``onreceiveitem`` callback handle that.

wxdo.workerthread
=================

This module is mostly an implementation detail for *wxdo.wxqueue*.  It's a
self-closing background thread that work items can be posted to.


Cleanup
-------

The queue can be explicitly unbound from the ``wx.Window``, along with the
callback, using the ``Unbind`` method, if for some reason you no longer want it
to receive queued items.  It can then be rebound to a different ``wx.Window``
using the ``BindReceiveItem`` method.

There is usually no need to do that, though.

When the ``wx.Window`` is destroyed, remaining items in the queue are left
unprocessed, ensuring that the ``onreceiveitem`` callback is never called when
the ``wx`` objects it's updating no longer exist.


wxdo.sizers
===========
The sizers module contains a few utility functions to work with sizers.

Functions
---------

SetSizerNaturalTabOrder
+++++++++++++++++++++++
When ``wx.Window`` objects are moved around, the tab order gets messed up.
This function restored the tab order for all windows in a sizer hierarchy to the
natural left-to-right, top-to-bottom order.


About/license
=============
wxdo is copyright Flonidan A/S (https://www.flonidan.dk/) and released under the MIT license.

Written by Anders Munch (ajm@flonidan.dk).

Additional credits: None yet, but contributions welcome.
