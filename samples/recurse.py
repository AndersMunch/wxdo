# Example of a more complicated application:
# - Recursive application: You can add a DeepObjectList as an element of another DeepObjectList.
# - Instead of using a default-valued object, CreateObject puts up a dialog to select a specific value.
#   Therefore, Colour.unknown is no longer needed, like it was in readme_example.py.
# - List_ItemEditor.Create: An item editors with multiple columns.
# - List_ItemEditor.Create: The widgets for a column can be both wx.Window and wx.Sizer.

import sys, os
sys.path.insert(0, '..')
import wx
from enum import Enum, auto
from wxdo.deep_object_list import DeepObjectList, DeepObjectList_Parameters, DeepObjectItemEditor, CancelOperation

class Colour(Enum):
   white = auto()
   black = auto()
   red = auto()
   green = auto()
   blue = auto()
   yellow = auto()

class Parameters(DeepObjectList_Parameters):
    def CreateObject(self, parent):
        with wx.SingleChoiceDialog(
            parent,
            'What would you like to add?',
            '[+] menu',
            ['a list of colours within this one']
            + [e.name for e in Colour],
            wx.CHOICEDLG_STYLE) as dia:

            if dia.ShowModal() == wx.ID_OK:
                sel = dia.GetSelection()
                if sel == 0:
                    return []
                else:
                    return list(Colour)[sel-1]
            else:
                raise CancelOperation

    def CreateItemEditor(self, value):
        if isinstance(value, Colour):
            return Colour_ItemEditor()
        else:
            return List_ItemEditor(self)

    def GetColumnTitles(self, parent):
        return ['Variant', 'Value of variant']


class Colour_ItemEditor(DeepObjectItemEditor):
    def Create(self):
        # self.parent is the appropriate parent to use for wxPython windows.
        self._label = wx.StaticText(self.parent, -1, "simple")
        self._choice = wx.Choice(self.parent, -1, choices=list(Colour.__members__.keys()))
        # Return something that can be added to a sizer.
        return [self._label, self._choice]

    def Destroy(self):
        self._choice.Destroy()
        self._label.Destroy()

    def SetValue(self, value):
       position = list(Colour.__members__.values()).index(value)
       self._choice.SetSelection(position)

    def GetValue(self):
       position = self._choice.GetSelection()
       return list(Colour.__members__.values())[position]

    def NotifyPosition(self, index, bgcol):
       self._label.SetBackgroundColour(bgcol)


class List_ItemEditor(DeepObjectItemEditor):
    def __init__(self, parameters):
        self.parameters = parameters

    def Create(self):
        self._label_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self._label = wx.StaticText(self.parent, -1, "... nested: ")
        self._label_hbox.AddStretchSpacer(1)
        self._label_hbox.Add(self._label)
        self._sublist = DeepObjectList(self.parent, -1, self.parameters)
        self._sublist.SetTitleBackgroundColour('ORANGE')
        return [self._label_hbox, self._sublist]

    def Destroy(self):
        self._label.Destroy()
        self._sublist.Destroy()

    def SetValue(self, value):
        self._sublist.SetValue(value)

    def GetValue(self):
        return self._sublist.GetValue()

    def SetLayoutCallback(self, layout_callback):
        self._sublist.SetLayoutCallback(layout_callback)

    def NotifyPosition(self, index, bgcol):
       self._label.SetBackgroundColour(bgcol)



if __name__=='__main__':
    try:
        import wize as iz
    except ModuleNotFoundError:
        print('wxWize required - https://github.com/AndersMunch/wxWize - pip install wxWize')
    else:
        class DemoFrame(wx.Frame):
            def __init__(self):
                with iz.Frame(init=self), iz.Panel() as panel:
                    with iz.BoxSizer(wx.VERTICAL):
                        params = Parameters()
                        self._list_editor = DeepObjectList(iz.Parent(), -1, params)
                        self._list_editor.SetLayoutCallback(panel.Layout)
                        self._list_editor.SetTitleBackgroundColour('YELLOW')
                        iz.Panel(w=self._list_editor)
                        with iz.BoxSizer(wx.HORIZONTAL):
                            iz.Button("GetValue", EVT_BUTTON=self.OnGetValue)
                            iz.Button("SetValue", EVT_BUTTON=self.OnSetValue)
            def OnGetValue(self, event):
                wx.MessageBox("GetValue returned: %s" % (self._list_editor.GetValue(),))
            def OnSetValue(self, event):
                # Just a random value to show off SetValue creating a matching complex UI.
                self._list_editor.SetValue(
                    [
                     [Colour.white, Colour.black],
                     [Colour.red, Colour.green, [Colour.blue, Colour.yellow]],
                     [Colour.blue],
                     ])


        app = wx.App()
        fr = DemoFrame()
        fr.Show(True)
        app.MainLoop()
