"""!
@brief wx.Sizer utilities.
"""
import weakref
import wx


def SizerWindowsInLayoutOrder(top_sizer):
    """!
    @brief Enumerates the wx.Window's in a sizer hierarchy.
    @param[in] top_sizer	The root of a sizer hierarchy.
    @return yields wx.Window's top-down subsidiarily left-right, following the sizer order.
    """
    def visit_sizer(sz):
        if isinstance(sz, wx.GridBagSizer):
            for child in sorted(sz.GetChildren(), key=lambda si:(si.GetPos().GetRow(), si.GetPos().GetCol())):
                for x in visit_sizer_item(child): yield x
        elif isinstance(sz, (wx.BoxSizer, wx.FlexGridSizer)):
            for nr in range(sz.GetItemCount()):
                for x in visit_sizer_item(sz.GetItem(nr)): yield x
        elif isinstance(sz, wx.Sizer):
            raise NotImplementedError(sz)
        else:
            raise TypeError(sz)
    def visit_sizer_item(si):
        wi = si.GetWindow()
        if wi is not None:
            yield wi
        sz = si.GetSizer()
        if sz is not None:
            for x in visit_sizer(sz):
                yield x
    for x in visit_sizer(top_sizer):
        yield x


def SetSizerNaturalTabOrder(top_sizer):
    """
    @brief Update tab order.
    @param[in] top_sizer	The root of a sizer hierarchy.
    @par[Description]
    Changes the tab order of wx.Window's in a sizer hierarchy to the natural
    order based on the sizer position.
    """
    sibling = None
    for win in SizerWindowsInLayoutOrder(top_sizer):
        if win.AcceptsFocus():
            if sibling is not None:
                if sibling.GetParent() != win.GetParent():
                    # This is most like a bug, passing the wrong parent value in __init__.
                    raise ValueError("not the same parent?? %r->%r, %r->%r" % (sibling, sibling.GetParent(),
                                                                               win,win.GetParent()))
                else:
                    win.MoveAfterInTabOrder(sibling)
            sibling = win


def IterSizerChildren(sizer):
    """!
    @brief Enumerate wx.Window's in the sizer hierarchy.
    @param[in] sizer		wx.Sizer
    @return			Yields (wx.Sizer it belongs to,wx.Window) for each wx.Window found.
    """
    for ch in sizer.GetChildren():
        subsz = ch.GetSizer()
        if subsz is not None:
            for subsubsz,subsubw in IterSizerChildren(subsz):
                yield subsubsz,subsubw
        subw = ch.GetWindow()
        if subw is not None:
            yield sizer,subw


_hide_cache = weakref.WeakKeyDictionary() # dict(wx.Window => list of(weakref to wxwindow))
def SizerHide(in_sizer, wxobject):
    """!
    @brief  Same as in_sizer.Show(wxobject, False), except remembers which nested elements were hidden (for SizerShow).
    @param[in] in_sizer		The wx.Sizer which 'wxobject' is a member of.
    @param[in] wxobject		The wx.Sizer or wx.Window to hide.
    """
    if not isinstance(wxobject, wx.Window) and wxobject not in _hide_cache:
        record_hidden = [weakref.ref(subwin)
                         for subsz,subwin in IterSizerChildren(wxobject)
                         if not subwin.IsShown()]
        _hide_cache[wxobject] = record_hidden
    in_sizer.Show(wxobject, False)


def SizerShow(in_sizer, wxobject):
    """!
    @brief Shows a wx.Window or wx.Sizer.
    @description
        Like in_sizer.Show(wxobject,True), but takes the information from SizerHide into account, if found:
        Any windows that were hidden.

        Reverses SizerHide, as if , except keeps hidden what was hidden before SizerHide.
    @param[in] in_sizer		The wx.Sizer which 'wxobject' is a member of.
    @param[in] wxobject		The wx.Sizer or wx.Window to show.
    """
    if isinstance(wxobject, wx.Window):
        in_sizer.Show(wxobject, True)
    try:
        record_hidden = _hide_cache.pop(wxobject)
    except KeyError:
        in_sizer.Show(wxobject, True)
    else:
        tohide = set()
        for subwin_ref in record_hidden:
            subwin = subwin_ref()
            if subwin is not None:
                tohide.add(subwin)
        for subsz,subwin in IterSizerChildren(wxobject):
            if subwin in tohide:
                subsz.Show(subwin, False)
            else:
                subsz.Show(subwin, True)
        in_sizer.Layout()
