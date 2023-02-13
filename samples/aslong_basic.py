"""
wxdo.aslong sample.
"""
import sys
sys.path.insert(0, '..')
import time
import wx
import wize as iz
from wxdo import aslong

class AslongExFrame(wx.Frame):
    def __init__(self):
        with iz.Frame(init=self), iz.Panel():
            with iz.BoxSizer(wx.HORIZONTAL, proportion=1):
                iz.Button("Start", EVT_BUTTON=self.OnButton)
                self._edit = iz.TextCtrl(
                    "This text will be changed from the background thread.",
                    style=wx.TE_READONLY, proportion=1).wx

    @aslong.task
    async def OnButton(self, event):
        await aslong.bg()
        t0 = time.time()
        while 1:
            time.sleep(0.1)
            elapsed = time.time()-t0
            async with aslong.ui:
                self._edit.SetValue('%.1f seconds elapsed' % (elapsed,))
            if elapsed > 10:
                break

app = wx.App()
fr = AslongExFrame()
fr.Show(True)
app.MainLoop()
