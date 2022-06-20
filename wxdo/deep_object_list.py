"""List control that allows for arbitrary wxPython things as list elements."""
import sys, os.path, struct, re, itertools, io, binascii, time
import wx
from .sizers import SetSizerNaturalTabOrder

def _Bitmap(b64data):
    return wx.Bitmap(wx.Image(io.BytesIO(binascii.a2b_base64(b64data))))
# Freeware icons from https://findicons.com/, scaled down to 12-16 pixels.
_add_12_bm_b64 = """
iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAABmJLR0QA/wD/AP+gvaeTAAAACXBI
WXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5AoHCygSNNfjLwAAAR1JREFUKM+NkbEuRFEURde5784z
RmQySBREiEKhUYlK6yPEJ2j9Dx8hfmA0GhGmEySChMR4BvPe3HOOQsNMgt3uvZq1haFsH6375uoa
AO3OOQdbx/K9j8PAVGOam/KAGHKey8ZwPQqYCWPZBHiOWfYfwPioMkQyko7skZ3DDW81A07AHKYm
696LF+IWub4rvWGLkkxxh6dujzjbqqPNU4LnVAZdj6KphhrMzIxLP92SGag5ZWHElDJcxzDJcRcq
NdSEpGAO5jXMBQdUK+LJ6T1vGhBRBGF5bslr81ciRDpnH14Wgy+tAi+FEtu7nR+eF/ZX3JIQEIru
QC73nn//QYgM1AgSMONvrQ4kDYTguP8DeHh8otfvgwx4f00jwCek6oxsQJsrjAAAAABJRU5ErkJg
gg==
"""
_erase_12_bm_b64 = """
iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAABmJLR0QA/wD/AP+gvaeTAAAACXBI
WXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5AoHCycyiCHfKAAAAc1JREFUKM9tkE9I03EAxd/X359t
v/22fq451xJtE0lDsA6GBJlFDDJsGWaBKB5CvUjQoUvnbtk1hMKDl0QIs4IiDxUURFQUHcrCmsM/
tTTn3M/fb/+eh7C/vuN7nwePJ9jZ24SqnceKifmUdHPkqt19Do7R6/hXr091dtm5nEtw5BoRdAIW
UHgx8zn99OVeefu2dBp5hG6NM9HVO6zV1fYZATdWLPO54OWLCwhoQayagKwwl1KZuTNVb7u1kHZg
/5RH98J+9waJZLK95uGDCcG65hBO7LmLUsc+ZCxgvYCcsxzC64M8/ZHW3Nf5G7Px3a27KszIvUmC
R2MAAEZbTxZ7YstsayYbG8hwmEte3ysAmD4cxZbKeIzbPH6QrNxB+gNccrrzk1CNZ1D+h7NQr7Cv
jaz20y4rJQ2D9Pj4QSjv/wIJIQi0cKCDbCgnawL8Dun0AuQjdHpJVed9SOf/KMDBjih5KEw2VRUt
Q3+0mc1A7qfqYVxycNMrAdyDqJABSQHTtvi0shZLQgUARJAf/pI1xyp1DRPAhZ8Fl8vGt0VALUE+
vjpUD6TKkP21IIzC2R+WZda6lDO/Z0WCQwW/cWmr5x5DEU+Alre6tgwAG3nqwMHMZzz0AAAAAElF
TkSuQmCC
"""
_up_down_16_bm_b64 = """
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAR0lEQVQoz81QywoAMAjS0f//sjsM
WtCDHeclSssKeIRSrlNbTqvuXIFSLdBgBMBAJ9hZjPhBYONXVU+I57K24I3dDuwel7AB09oNGgwg
x1gAAAAASUVORK5CYII=
"""
_hand_bm_b64 = """
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAABqUlE
QVQ4y6WSsWtUQRCHvxMLawtBECRYWAhXBAlECCiIoFXgCJx/wntgYWMjaGUXMGB4z0bByjSBQEAQ
tJAQE5QUCVoJQQvBIiLJu5eX3ZnZtbjcweXexYADy49lZj9mfzONGCP/E6dHJd5kdzMgAfI76et0
VN2pUQkLMTk3dh0LMVmeb8fl+XZ2IsDS3Ey2NDcTTa0LUuP8pRuYWnIigGlILly+iWno3fu6ONuK
i7Ot7FiAqEKQWr145RaimhwPECOaq1fpIGLDU3j56HbfcYAo1eGDeh3qQLwmzclpxGsiXjGpaE5O
Y37/UEvEa1+HAaL5+rsFxqdaiCjRDLfzDXUl1a8vSFV0c1WByCCg0dvEp/em4tWJa5w5O4b7vY1U
f7CDghAEQgS6dV+/73D/2UpjyEQRy9dWV3C7PzF1+P0OvtzFl3u4zh6uLHBlUe8BwIPnH1MRzT+8
f4scVJgIogHxhpqi2j1HvzAwxocvPqWqhniPWsRCJISAacQ0sPWjQNXyf21ivvZ5E0IgWEQ1YqaY
GaaBx6820loTBzppN3t7cTTyJwtbA4C/VFlRST2YwJsAAAAASUVORK5CYII=
"""

ID_MOVE_UP = wx.NewIdRef()
ID_MOVE_DOWN = wx.NewIdRef()
ID_CANCEL_SELECT = wx.NewIdRef()

class CancelOperation(Exception):
    """!
    @brief CreateObject cancellation exception.
    """
    pass

class DeepObjectItemEditor:
    """!
    @brief Defines the wxPython components to display and edit a list item.
    """
    def __init__(self):
        self.__layout_callback = None

    def Create(self):
        """!
        @brief Create wxPython windows.
        @return A list of items that can be added to sizers, or None, to skip a column.
        @param[in] self.parent		wxPython parent.
        @param[in] self.readonly	If True, request read-only controls to be created.
        @par[Description]
            Never call this directly, go through CreateOnto.
            Items returned can be:
            - None: Skip the column.
            - A wx.Window
            - A wx.Sizer
            - A dict of named Sizer.Add arguments.
        """
        raise NotImplementedError

    def Destroy(self):
        """!
        @brief Destroy or hide the wxPython windows that self.Create created.
        @par[Description]
            Only used when entries are deleted from the list.  Not called when the list
            itself is destroyed, standard wxPython parenting handles that.
        """
        raise NotImplementedError

    def SetValue(self, value):
        """!
        @brief Change the displayed value.
        @par[Description]
            Implement in subclass.
        """
        raise NotImplementedError

    def GetValue(self):
        """!
        @brief Read the value from the GUI components.
        @par[Description]
            Implement in subclass.
            Note: SetValue is always called before any call to GetValue.
        """
        raise NotImplementedError

    def CreateOnto(self, parent, readonly):
        """!
        @return A list of items that can be added to sizers.
        @par[Description]
        For internal use only.
        """
        self.parent = parent
        self.readonly = readonly
        return self.Create()

    def SetLayoutCallback(self, layout_callback):
        """!
        @brief Set callback for when the size of the controls change.
        """
        self.__layout_callback = layout_callback

    def LayoutCallback(self):
        """!
        @brief Notify that the size of the controls have changed, and a Layout may be necessary.
        """
        if self.__layout_callback is not None:
            self.__layout_callback()

    def NotifyPosition(self, index, bgcol):
        """!
        @brief Inform a newly created or moved editor of its position.
        @param[in] index	0-based index into the full list.
        @param[in] bgcol	The background colour for that position.
        """
        pass


class DeepObjectList_Parameters:
    """!
    @brief Parameters for DeepObjectList.
    @par[Description] 
        What is termed an 'object' in this context is a member of the list assigned with SetValue
        and retrieved with GetValue.
    """

    def CreateObject(self, parent):
        """!
        @brief Create a new list item.
        @param[in] parent	wxPython parent (the [+] button that was pressed).
        @return A list item value.
        @par[Description]
            To cancel creating an object, raise the CancelOperation exception.
        """
        raise NotImplementedError

    def ConfirmErase(self, parent, rowno, value):
        """!
        @brief Confirm deleting an entry.
        @param[in] parent	wxPython parent for use in a confirmation dialogue.
        @param[in] rowno	Position in list, 0-
        @param[in] value	The value of the object to erase, or None if DeepObjectItemEditor.GetValue failed.
        @retval True	OK to delete.
        @retval False	Cancel delete.
        """
        return True

    def CreateItemEditor(self, obj):
        """!
        @brief 
        @param[in] obj	An object to be displayed/edited.
        @return A DeepObjectItemEditor suitable for editing this object.
        """
        raise NotImplementedError

    def GetColumnTitles(self, parent):
        """!
        @brief Optional column titles, corresponding to the sizer items returned by DeepObjectItemEditor.Create.
        @param[in] parent	wxPython parent.
        @return A list, elements can be None, str, wx.Sizer or wx.Window.
        """
        return []

    def GetEraseAllowed(self):
        """!
        @brief Whether list items can be erased.
        """
        return True

    def GetAddAllowed(self):
        """!
        @brief Whether list items can be added.
        """
        return True

    def GetReorderAllowed(self):
        """!
        @brief Whether list items can be moved up and down.
        """
        return True


class _Item:
    # Bookkeeping for an entry in the list.
    def __init__(self, params, parent, readonly, initial_obj):
        self.parent = parent
        self.sizer_items = []
        self.gbz_positions = [] # list of (x,sizer_item) of things to move with the item
        self.widget = params.CreateItemEditor(initial_obj)
        self.sizer_items = self.widget.CreateOnto(parent, readonly)
        self._original_obj = initial_obj
        self.widget.SetValue(initial_obj)
        self.rowno = None
        self.buttons = []

    def GetValue(self):
        return self.widget.GetValue()

    def SetValue(self, obj):
        self.widget.SetValue(obj)

    def Destroy(self):
        self.widget.Destroy()
        for but in self.buttons:
            but.Destroy()


class DeepObjectList(wx.Panel):
    """!
    @brief Edit as list of objects.
    """

    # SetText-overridable UI texts.
    _hint_add = "Add new"
    _hint_erase = "Erase"
    _hint_up_down = "Move up/down"

    # SetColours-overriable colours. Default, super-discrete white-greys.
    # Alternative: _even_bg,_odd_bg = '#aabbaa','#cccccc'
    _even_bg = '#eeeeee'
    _odd_bg = '#fcfcfc'
    

    @classmethod
    def SetTexts(cls, hint_add=None, hint_erase=None, hint_up_down=None):
        """!
        @brief i18n texts.
        """
        cls._hint_add = hint_add or cls._hint_add
        cls._hint_erase = hint_erase or cls._hint_erase
        cls._hint_up_down = hint_up_down or cls._hint_up_down

    @classmethod
    def SetColours(cls, even_bg=None, odd_bg=None, title_bg=None):
        cls._even_bg = even_bg or cls._even_bg
        cls._odd_bg = odd_bg or cls._odd_bg
        cls._title_bg = title_bg or cls._title_bg

    def __init__(self, parent, id, param, readonly=False, initial_value=None):
        super().__init__(parent, id)
        self._param = param
        self._items = [] # list of _Item
        self._item_wxparent = self
        self._layout_callback = None
        self._fixed_adds = [] # list of (x,y,sizer_item) for permanent decoration
        self._append_but = None # last-line append button
        self._readonly = readonly
        self._title_background_colour = None # defaults to background
        self._growable_cols = set()

        # Coordinate drag and drop:
        self._buttondown_item = None # item under the cursor at EVT_LEFT_DOWN
        self._buttonup_time = None
        self._move_select_items = set()

        self._add_bm = _Bitmap(_add_12_bm_b64)
        self._erase_bm = _Bitmap(_erase_12_bm_b64)
        self._up_down_bm = _Bitmap(_hand_bm_b64)
        self._up_down_selected_bm = _Bitmap(_up_down_16_bm_b64)

        # Create the GUI structure.
        self._x0 = 0
        self._y0 = 0
        if param.GetAddAllowed():
            self._add_col = self._x0
            self._x0 += 1
        if param.GetEraseAllowed():
            self._erase_col = self._x0
            self._x0 += 1
        if param.GetReorderAllowed():
            self._up_down_col = self._x0
            self._x0 += 1
        # self._x0 = the first column number for the user controls created by DeepObjectItemEditor

        gbz = self._gbz = wx.GridBagSizer()
        self.SetSizer(gbz)

        cts = param.GetColumnTitles(parent=self)
        if len(cts)!=0:
            for colno,title in enumerate(cts):
                if title is None:
                    continue
                if isinstance(title, str):
                    st = wx.StaticText(self, -1, title)
                else:
                    assert isinstance(title, (wx.Sizer, wx.Window))
                    st = title
                x = self._x0 + colno
                gbz.Add(st, pos=(self._y0, x))
                self._fixed_adds.append((x, self._y0, st))
            self._y0 += 1
        # self._y0 = the row number of the first list entry

        if self._add_col is not None:
            bm_sz = self._add_bm.GetSize()
            but = wx.BitmapButton(self._item_wxparent, -1, self._add_bm, size=(bm_sz.Width+10, bm_sz.Height+10))
            but.SetToolTip(self._hint_add)
            but.Bind(wx.EVT_BUTTON, self._OnAppendNew)
            self._append_but = but
        else:
            self._append_but = None

        self.Bind(wx.EVT_ERASE_BACKGROUND, self._OnEraseBackground)

        self._normal_acc = wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_DOWN, ID_MOVE_DOWN),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_UP, ID_MOVE_UP),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, ID_CANCEL_SELECT)
            ])
        self._alt_acc = wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_DOWN, ID_MOVE_DOWN),
            wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_UP, ID_MOVE_UP),
            ])

        # Wanted to use wx.ACCEL_NORMAL here, but that would interfere with list item
        # editing controls that use arrow up/down also.
        self.SetAcceleratorTable(self._alt_acc)

        self.Bind(wx.EVT_MENU, self._OnDown, id=ID_MOVE_DOWN)
        self.Bind(wx.EVT_MENU, self._OnUp, id=ID_MOVE_UP)
        self.Bind(wx.EVT_MENU, self._OnCancelSelect, id=ID_CANCEL_SELECT)

        if initial_value is None:
            self.SetValue([])
        else:
            self.SetValue(initial_value)

    def _OnCancelSelect(self, event):
        for it in self._move_select_items:
            self._show_move_icon(it, False)
        self._move_select_items.clear()

    def SetTitleBackgroundColour(self, col):
        self._title_background_colour = col

    def _OnEraseBackground(self, event):
        # How wx.lib.agw.customtreectrl does it.
        dc = event.GetDC()
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRegion(rect)

        def pen_brush(col):
            return wx.Pen(col), wx.Brush(col, wx.BRUSHSTYLE_SOLID)
        bgcol = self.GetBackgroundColour()
        if self._title_background_colour is None:
            title_col = bgcol
        else:
            title_col = self._title_background_colour
        pen_title,brush_title = pen_brush(title_col)
        pen_even,brush_even = pen_brush(self._even_bg)
        pen_odd,brush_odd = pen_brush(self._odd_bg)
        pen_other,brush_other = pen_brush(bgcol)

        y0 = sum(self._gbz.GetCellSize(y, 0).Height for y in range(self._y0))
        width,height = self.GetSize()

        dc.SetPen(pen_title)
        dc.SetBrush(brush_title)
        dc.DrawRectangle(0, 0, width, y0)

        max_row = self._gbz.GetRows()
        y = y0
        for nr in range(len(self._items) + (1 if self._param.GetAddAllowed() else 0)):
            row = self._y0+nr
            if row >= max_row:
                continue
            h = self._gbz.GetCellSize(row, 0).Height
            dc.SetPen([pen_even, pen_odd][nr % 2])
            dc.SetBrush([brush_even, brush_odd][nr % 2])
            dc.DrawRectangle(0, y, width, h)
            y += h

        if height > y:
            dc.SetPen(pen_other)
            dc.SetBrush(brush_other)
            dc.DrawRectangle(0, y, width, height-y)


    def SetLayoutCallback(self, callback):
        self._layout_callback = callback

    def SetValue(self, val):
        """
        @brief Assigns a value to the control.
        @param[in] val		A list of objects.
        """
        if len(self._items) > 0:
            for it in self._items:
                it.Destroy()
            self._items = []

        pa = self._param
        for item_val in val:
            self._items.append(self._create_item(item_val))

        self._rebuild_gbz(size_change=len(self._items))

    def _create_item(self, item_val):
        it = _Item(self._param, self._item_wxparent, self._readonly, item_val)
        it.widget.SetLayoutCallback(self._layout_callback)
        for colno,szi in enumerate(it.sizer_items):
            if szi is not None:
                x = self._x0 + colno
                it.gbz_positions.append((x,szi))
        for col,hint,mk_handler,bm in [
            (self._add_col, self._hint_add, self._mkOnAddBefore, self._add_bm),
            (self._erase_col, self._hint_erase, self._mkOnErase, self._erase_bm),
            (self._up_down_col, self._hint_up_down, None, self._up_down_bm),
            ]:
            if col is not None:
                but = wx.BitmapButton(self._item_wxparent, -1, bm, size=(bm.GetWidth()+10, bm.GetHeight()+10))
                but.SetAcceleratorTable(self._normal_acc)
                but.SetToolTip(hint)
                if mk_handler is not None:
                    but.Bind(wx.EVT_BUTTON, mk_handler(but, it))
                else:
                    it.move_button = but
                    but.Bind(wx.EVT_LEFT_DOWN, self._mk_On_UpDown_buttondown(but, it))
                    but.Bind(wx.EVT_LEFT_UP, self._mk_OnUpDown_buttonup(but, it))
                    but.Bind(wx.EVT_BUTTON, self._mk_OnUpDown_buttonpress(but, it))
                it.buttons.append(but)
                it.gbz_positions.append((col,but))
        return it

    def _rebuild_gbz(self, size_change):
        changed_rows = self._renumber_items()
        gbz = self._gbz

        rowheights_before = gbz.GetRowHeights()

        # Detach all sizers and windows from the GridBagSizer without destroying them.
        for i in reversed(range(gbz.GetItemCount())):
            gbz.Detach(i)

        # Re-add them, potentially in a different order, and with additions and deletions.
        for x,y,sz_it in self._fixed_adds:
            self._gbz.Add(sz_it, pos=(y,x), border=3, flag=wx.ALL)
        for it in self._items:
            for x,sz_it in it.gbz_positions:
                Add_args = dict(flag=0)
                if x < self._x0:
                    Add_args['border'] = 3
                    Add_args['flag'] = wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL
                else:
                    Add_args['border'] = 3
                    Add_args['flag'] |= wx.ALL
                if isinstance(sz_it, dict):
                    Add_args.update(sz_it)
                    try:
                        w = Add_args.pop('window')
                    except KeyError:
                        w = Add_args.pop('sizer')
                    expand = (Add_args['flag'] & wx.EXPAND) != 0
                else:
                    w = sz_it
                    expand = False

                self._gbz.Add(w, pos=(self._y0+it.rowno, x), **Add_args)
                if expand and x not in self._growable_cols:
                    self._growable_cols.add(x)
                    self._gbz.AddGrowableCol(x)

        if self._append_but is not None:
            lastline_y = self._y0 + len(self._items)
            self._gbz.Add(self._append_but, pos=(lastline_y, self._add_col),
                          border=3, flag=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        SetSizerNaturalTabOrder(gbz)
        gbz.Layout()

        if size_change != 0 and self._layout_callback is not None:
            self._layout_callback()
            # The width available to the gbz may have changed, requiring a Refresh.
            # However, we assume that whatever Refresh is necessary has been trigged by the callback.

        # A full self.Refresh() causes flicker, so compute the precise refresh needed and do a more
        # limited RefreshRect.
        #
        # Unfortunately it seems like something else is triggering a full refresh, and this code has
        # little or no effect. Is it self._gbz.Layout()? Or self._gbz.Add? Dunno.
        #
        if len(changed_rows)>0 or size_change != 0:
            rowheights_after = gbz.GetRowHeights()
            panel_size = self.GetSize()

            if len(changed_rows) > 0:
                min_ch_row = min(changed_rows)
            elif size_change > 0:
                min_ch_row = len(self._items) - size_change
            else:
                min_ch_row = len(self._items)
            y_top = sum(rh for rh in rowheights_after[:self._y0 + min_ch_row])

            if size_change < 0:
                # Redraw includes erased space after a delete.
                y_bottom = max(sum(rowheights_before), sum(rowheights_after))
            else:
                y_bottom = sum(rowheights_after[:self._y0 + max(changed_rows) + 1])

            if y_bottom > y_top:
                self.RefreshRect(
                    wx.Rect(
                        0,			# x
                        y_top,			# y
                        panel_size.Width,	# width
                        y_bottom-y_top,		# height
                        ))
            


    def _renumber_items(self):
        # Align item.rowno with the actual position in self._items.
        changed_rows = []
        for rowno,it in enumerate(self._items):
            if it.rowno != rowno:
                changed_rows.append(rowno)
                it.widget.NotifyPosition(index=rowno, bgcol=self._even_bg if rowno%2==0 else self._odd_bg)
            it.rowno = rowno
        return changed_rows
            

    def _mkOnAddBefore(self, but, item):
        def OnAddBefore(event):
            try:
                new_obj = self._param.CreateObject(but)
            except CancelOperation:
                pass
            else:
                self._items.insert(item.rowno, self._create_item(new_obj))
                self._rebuild_gbz(size_change=+1)
        return OnAddBefore

    def _OnAppendNew(self, event):
        try:
            new_obj = self._param.CreateObject(self)
        except CancelOperation:
            pass
        else:
            self._items.append(self._create_item(new_obj))
            self._rebuild_gbz(size_change=+1)

    def _show_move_icon(self, item, i_move):
        if i_move:
            item.move_button.SetBitmap(self._up_down_selected_bm)
        else:
            item.move_button.SetBitmap(self._up_down_bm)
        item.move_button.Refresh()

    def _item_for_y(self, y):
        #@param[in] y		Vertical position in pixels.
        #@return The _Item at that position or None if above or below the list.
        y0 = sum(self._gbz.GetCellSize(y, 0).Height for y in range(self._y0))
        if y < y0:
            return None
        else:
            y_item = y0
            for nr,it in enumerate(self._items):
                h = self._gbz.GetCellSize(self._y0+nr, 0).Height
                if y < y_item + h:
                    return it
                y_item += h
        return None

    def _mk_On_UpDown_buttondown(self, but, item):
        def On_UpDown_buttondown(event):
            event.Skip()
            self._buttondown_item = item
            self._show_move_icon(item, True)
        return On_UpDown_buttondown

    def _mk_OnUpDown_buttonup(self, but, item):
        def OnUpDown_buttonup(event):
            event.Skip()
            self._buttonup_time = time.monotonic()
            up_item = self._item_for_y(but.GetPosition().y + event.y)
            if up_item is not None and up_item != item:
                # EVT_LEFT_UP on a different item than EVT_LEFT_DOWN: That's a drag.
                self._items.insert(up_item.rowno, self._items.pop(item.rowno))
                for it in self._move_select_items:
                    self._show_move_icon(it, False)
                self._move_select_items.clear()
                self._rebuild_gbz(size_change=0)

            elif up_item is not None and up_item == self._buttondown_item:
                self._flip_move_button_status(item)

            self._show_move_icon(item, item in self._move_select_items)
        return OnUpDown_buttonup

    def _mk_OnUpDown_buttonpress(self, but, item):
        def OnUpDown_buttonpress(event):
            # Using a timeout to distinguish between keyboard button presses and mouse button
            # presses, which is suspect - there must be a more direct way to do this?!
            # The problem scenario is a mouse button press where the mouse
            # leaves the button before the mouse-up, thus not creating a
            # button-press event, and then the user does a keypress.  Can't
            # have that keypress ignored because it's taken to be an already
            # handled mouse action.
            # Not doing event.Skip() in the up/down events would get rid of the
            # EVT_BUTTON, but that has other side-effects.
            if self._buttonup_time is not None and time.monotonic()-self._buttonup_time < 1.0:
                # Skip, this is a mouse action already handled in EVT_LEFT_UP event.
                self._buttonup_time = None
            else:
                # Keyboard button activation.
                self._flip_move_button_status(item)
        return OnUpDown_buttonpress

    def _movable_subset(self, moving_down):
        # If there are gaps in the selected items, then only move a connected
        # subset, either at the top or the bottom.
        move_items = sorted(self._move_select_items, key=lambda it:it.rowno)
        first_pos = 0
        for pos, it in enumerate(move_items):
            if pos > 0:
                if it.rowno == move_items[pos-1].rowno + 1:
                    pass # Sequential, OK.
                else:
                    if moving_down:
                        # Non-sequential: Delete any that follow the sequential prefix.
                        del move_items[pos:]
                        return move_items
                    else:
                        first_pos = pos
        del move_items[:first_pos]
        return move_items

    def _OnUp(self, event):
        if len(self._move_select_items)==0:
            event.Skip()
        else:
            move_items = self._movable_subset(moving_down=False)
            insert_at = move_items[0].rowno - 1
            if insert_at >= 0:
                for item in reversed(move_items):
                    del self._items[item.rowno]
                self._items[insert_at:insert_at] = move_items
                self._rebuild_gbz(size_change=0)

    def _OnDown(self, event):
        if len(self._move_select_items)==0:
            event.Skip()
        else:
            move_items = self._movable_subset(moving_down=True)
            insert_at = move_items[0].rowno + 1
            if insert_at < len(self._items):
                for item in reversed(move_items):
                    del self._items[item.rowno]
                self._items[insert_at:insert_at] = move_items
                self._rebuild_gbz(size_change=0)

    def _flip_move_button_status(self, item):
        if item in self._move_select_items:
            self._move_select_items.remove(item)
            self._show_move_icon(item, False)
        else:
            self._move_select_items.add(item)
        self._show_move_icon(item, item in self._move_select_items)

    def _mkOnErase(self, but, item):
        def OnErase(event):
            assert item is self._items[item.rowno]
            try:
                val = item.GetValue()
            except:
                # If GetValue() fails for any reason, it must not stand in the way of erasing
                # the element, otherwise bad data might cause an un-erasable item.
                val = None
            else:
                if not self._param.ConfirmErase(but, item.rowno, val):
                    return
            item.Destroy()
            del self._items[item.rowno]
            if item in self._move_select_items:
                self._move_select_items.discard(item)
            item.rowno = "formerly %s" % (item.rowno,) # for debugging
            self._rebuild_gbz(size_change=-1)
        return OnErase

    def GetValue(self):
        """!
        @brief Read the displayed/edited value from the GUI components.
        @return List of objects.
        """
        return [it.GetValue() for it in self._items]

    def GetItemEditors(self):
        """!
        @brief Get the object editors for the list as it currently stands.
        @return A list of DeepObjectItemEditor.
        """
        return [it.widget for it in self._items]
