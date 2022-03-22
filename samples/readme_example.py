# This is the example from README.rst, made up to be a complete, free-standing application.  wxWize required.
import sys
sys.path.insert(0, '..')
import wx
from enum import Enum, auto
from wxdo.deep_object_list import DeepObjectList_Parameters, DeepObjectItemEditor
from wxdo.wize import DeepObjectList

class Colour(Enum):
   unknown = auto()
   white = auto()
   black = auto()
   red = auto()
   green = auto()
   blue = auto()
   yellow = auto()

class Parameters(DeepObjectList_Parameters):
   def CreateObject(self, parent):
       return Colour.unknown

   def CreateItemEditor(self, value):
       return Colour_ItemEditor()

class Colour_ItemEditor(DeepObjectItemEditor):
    def Create(self):
        # self.parent is the appropriate parent to use for wxPython windows.
        self._choice = wx.Choice(self.parent, -1, choices=list(Colour.__members__.keys()))
        # Return something that can be added to a sizer.
        return [self._choice]

    def Destroy(self):
        self._choice.Destroy()

    def SetValue(self, value):
       position = list(Colour.__members__.values()).index(value)
       self._choice.SetSelection(position)

    def GetValue(self):
       position = self._choice.GetSelection()
       return list(Colour.__members__.values())[position]

if __name__=='__main__':
    try:
        import wize as iz
    except ModuleNotFoundError:
        print('wxWize required - https://github.com/AndersMunch/wxWize - pip install wxWize')
    else:
        class DemoFrame(wx.Frame):
            def __init__(self):
                with iz.Frame(init=self):
                    with iz.BoxSizer(wx.VERTICAL):
                        params = Parameters()
                        self._list_editor = iz.DeepObjectList(params).wx
                        with iz.BoxSizer(wx.HORIZONTAL):
                            iz.Button("GetValue", EVT_BUTTON=self.OnGetValue)
                            iz.Button("SetValue", EVT_BUTTON=self.OnSetValue)
            def OnGetValue(self, event):
                wx.MessageBox("GetValue returned: %s" % (self._list_editor.GetValue(),))
            def OnSetValue(self, event):
                self._list_editor.SetValue([Colour.red, Colour.green, Colour.yellow])


        app = wx.App()
        fr = DemoFrame()
        fr.Show(True)
        app.MainLoop()
