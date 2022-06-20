wxdo
====

A small wxPython component library.

* ``wxdo.deep_object_list``: A widget for editing a list of arbitrary content.
* ``wxdo.sizers``: Sizer utilities.

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
