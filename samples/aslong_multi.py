"""
wxdo.aslong sample.
"""

import sys
sys.path.insert(0, '..')
import time, textwrap
import wx
import wize as iz
from wxdo import aslong


class AslongExampleFrame(wx.Frame):
    def __init__(self):
        with iz.Frame(init=self), iz.Panel(orient=wx.VERTICAL):
            iz.ExpandoTextCtrl(textwrap.dedent("""\
                Each button runs a background task that updates the gauge.
                They all share the same background thread.
                The first button only runs the task if the background thread is not busy."""),
                style=wx.TE_READONLY, flag=wx.EXPAND)
            with iz.BoxSizer(wx.HORIZONTAL, border=10):
                iz.Button("Run?", EVT_BUTTON=self.OnRunIfAvailable)
                self._gauge1 = iz.Gauge(proportion=1, flag=wx.EXPAND).wx

            iz.StaticLine(5)

            iz.ExpandoTextCtrl(textwrap.dedent("""\
                The second runs the background task even if it's already running.
                The progress bar will be erratic when there's more than one, but it won't crash, everything is nicely serialised."""),
                style=wx.TE_READONLY, flag=wx.EXPAND)
            with iz.BoxSizer(wx.HORIZONTAL, border=10):
                iz.Button("Run!", EVT_BUTTON=self.OnRunAlways)
                self._gauge2 = iz.Gauge(proportion=1, flag=wx.EXPAND).wx

            iz.StaticLine(5)

            iz.ExpandoTextCtrl(textwrap.dedent("""\
                The third continues to run the background task even if the frame is closed.
                It does this by trapping the TaskInterruptedError that .ui() produces when in .cleanup.
                The task must avoid UI interaction, but the background work can be completed."""),
                style=wx.TE_READONLY, flag=wx.EXPAND)
            with iz.BoxSizer(wx.HORIZONTAL, border=10):
                iz.Button("Run stubbornly!", EVT_BUTTON=self.OnRunStubbornly)
                self._gauge3 = iz.Gauge(proportion=1, flag=wx.EXPAND).wx

            iz.StaticLine(5)

            iz.ExpandoTextCtrl(textwrap.dedent("""\
                When the box is checked, the frame will close despite tasks still running.
                The first two tasks will then be interrupted mid-way."""),
                style=wx.TE_READONLY, flag=wx.EXPAND)
            self._allow_close_check = iz.CheckBox("Close despite background tasks running?", border=10).wx

            iz.StaticLine(5)

            self._message = iz.TextCtrl(style=wx.TE_READONLY, flag=wx.EXPAND, border=10).wx

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Layout()
        self.Fit()
        self.Layout()
        self.Fit()

    def OnClose(self, event):
        if event.CanVeto() and aslong.busy(self) and not self._allow_close_check.GetValue():
            event.Veto()
            self._message.SetValue("I'm working here .. don't close me now!")
        else:
            aslong.cleanup(self)
            self.Destroy()

    @aslong.task
    async def OnRunIfAvailable(self, event):
        if aslong.busy(self):
            self._message.SetValue("I'm busy! Can't start something now.")
        else:
            self._message.SetValue("Not doing anything else, let's go.")
            await self._Run(self._gauge1)

    @aslong.task
    async def OnRunAlways(self, event):
        if aslong.busy(self):
            self._message.SetValue("Running more than one thing at time.")
        else:
            self._message.SetValue("Running")
        await self._Run(self._gauge2)

        
    async def _Run(self, gauge):
        N = 100
        dT = 0.1
        gauge.SetRange(N)
        await aslong.bg()
        for step in range(1, N+1):
            time.sleep(dT)
            async with aslong.ui:
                gauge.SetValue(step)
        
        
    @aslong.task
    async def OnRunStubbornly(self, event):
        self._message.SetValue("I know he can get the job.  But can he finish the job?")
        self._allow_close_check.SetValue(True)
        N = 10
        dT = 1.0
        gauge = self._gauge3
        gauge.SetRange(N)
        await aslong.bg()
        update_gauge = True
        for step in range(1, N+1):
            print(f"Stubbornly running step {step} of {N}")
            time.sleep(dT)
            if update_gauge:
                try:
                    await aslong.ui()
                except InterruptedError:
                    print("The world is coming to an end?  See if I care.")
                    update_gauge = False
                else:
                    gauge.SetValue(step)
                    await aslong.bg()


app = wx.App()
fr = AslongExampleFrame()
fr.Show(True)
app.MainLoop()
