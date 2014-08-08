# -*- coding: utf-8 -*-

import sys

from meta import wx_minversion

import wxversion
if not getattr(sys, "frozen", False):
	wxversion.ensureMinimal("%i.%i" % wx_minversion[:2])
import wx
if wx.VERSION < wx_minversion:
	app = wx.PySimpleApp()
	result = wx.MessageBox("This application requires a version of wxPython "
						   "greater than or equal to %s, but your most recent "
						   "version is %s.\n\n"
						   "Would you like to download a new version of wxPython?\n"
						   % (".".join(str(n) for n in wx_minversion), wx.__version__),
						   "wxPython Upgrade Needed", style=wx.YES_NO)
	if result == wx.YES:
		import webbrowser
		webbrowser.open(wxversion.UPDATE_URL)
	app.MainLoop()
	sys.exit()
import wx.grid
from wx.lib.buttons import GenBitmapButton as _GenBitmapButton
from wx.lib.buttons import ThemedGenButton as _ThemedGenButton


def Property(func):
	return property(**func())


wx.BitmapButton._SetBitmapLabel = wx.BitmapButton.SetBitmapLabel

def SetBitmapLabel(self, bitmap):
	""" Replacement for SetBitmapLabel which avoids flickering """
	if self.GetBitmapLabel() != bitmap:
		self._SetBitmapLabel(bitmap)

wx.BitmapButton.SetBitmapLabel = SetBitmapLabel


def BitmapButtonEnable(self, enable = True):
	"""
	Replacement for BitmapButton.Enable which circumvents repainting issues
	
	(bitmap does not change on button state change)
	
	"""
	wx.Button.Enable(self, enable)
	if not hasattr(self, "_bitmaplabel"):
		self._bitmaplabel = self.GetBitmapLabel()
	if not hasattr(self, "_bitmapdisabled"):
		self._bitmapdisabled = self.GetBitmapDisabled()
	if enable:
		if not self._bitmaplabel.IsNull():
			self.SetBitmapLabel(self._bitmaplabel)
	else:
		if not self._bitmapdisabled.IsNull():
			self.SetBitmapLabel(self._bitmapdisabled)

def BitmapButtonDisable(self):
	"""
	Replacement for BitmapButton.Disable which circumvents repainting issues
	
	(bitmap does not change on button state change)
	
	"""
	self.Enable(False)

wx.BitmapButton.Enable = BitmapButtonEnable
wx.BitmapButton.Disable = BitmapButtonDisable


def FindMenuItem(self, label):
	""" Replacement for wx.Menu.FindItem """
	label = GTKMenuItemGetFixedLabel(label)
	for menuitem in self.GetMenuItems():
		if GTKMenuItemGetFixedLabel(menuitem.Label) == label:
			return menuitem.GetId()

wx.Menu.FindItem = FindMenuItem


def GTKMenuItemGetFixedLabel(label):
	if sys.platform not in ("darwin", "win32"):
		# The underscore is a special character under GTK, like the 
		# ampersand on Mac OS X and Windows
		# Recent wxPython versions already do the right thing, but we need
		# this workaround for older releases
		if "__" in label:
			label = label.replace("__", "_")
		while label and label[0] == "_":
			label = label[1:]
	return label


wx.Window._SetToolTipString = wx.Window.SetToolTipString

def SetToolTipString(self, string):
	""" Replacement for SetToolTipString which updates correctly """
	wx.Window.SetToolTip(self, None)
	wx.Window._SetToolTipString(self, string)

wx.Window.SetToolTipString = SetToolTipString


def GridGetSelection(self):
	""" Return selected rows, cols, block and cells """
	sel = []
	numrows = self.GetNumberRows()
	numcols = self.GetNumberCols()
	# rows
	rows = self.GetSelectedRows()
	for row in rows:
		if row > -1 and row < numrows:
			for i in range(numcols):
				if not (row, i) in sel:
					sel += [(row, i)]
	# cols
	cols = self.GetSelectedCols()
	for col in cols:
		if col > -1 and col < numcols:
			for i in range(numrows):
				if not (i, col) in sel:
					sel += [(i, col)]
	# block
	tl = self.GetSelectionBlockTopLeft()
	br = self.GetSelectionBlockBottomRight()
	if tl and br:
		for n in range(min(len(tl), len(br))):
			for i in range(tl[n][0], br[n][0] + 1): # rows
				if i > -1 and i < numrows:
					for j in range(tl[n][1], br[n][1] + 1): # cols
						if j > -1 and j < numcols and not (i, j) in sel:
							sel += [(i, j)]
	# single selected cells
	cells = self.GetSelectedCells()
	for cell in cells:
		if not -1 in cell and cell[0] < numrows and cell[1] < numcols and \
		   cell not in sel:
			sel += [cell]
	sel.sort()
	return sel

wx.grid.Grid.GetSelection = GridGetSelection


wx._ScrolledWindow = wx.ScrolledWindow

class ScrolledWindow(wx._ScrolledWindow):

	"""
	ScrolledWindow that scrolls child controls into view on focus.
	
	OnChildFocus and ScrollChildIntoView borrowed from wx.lib.scrolledpanel.
	"""

	def __init__(self, *args, **kwargs):
		wx._ScrolledWindow.__init__(self, *args, **kwargs)
		self.Bind(wx.EVT_CHILD_FOCUS, self.OnChildFocus)

	def OnChildFocus(self, evt):
		# If the child window that gets the focus is not visible,
		# this handler will try to scroll enough to see it.
		evt.Skip()
		child = evt.GetWindow()
		self.ScrollChildIntoView(child)

	def ScrollChildIntoView(self, child):
		"""
		Scrolls the panel such that the specified child window is in view.
		"""        
		sppu_x, sppu_y = self.GetScrollPixelsPerUnit()
		vs_x, vs_y   = self.GetViewStart()
		cr = child.GetRect()
		clntsz = self.GetClientSize()
		new_vs_x, new_vs_y = -1, -1

		# is it before the left edge?
		if cr.x < 0 and sppu_x > 0:
			new_vs_x = vs_x + (cr.x / sppu_x)

		# is it above the top?
		if cr.y < 0 and sppu_y > 0:
			new_vs_y = vs_y + (cr.y / sppu_y)

		# For the right and bottom edges, scroll enough to show the
		# whole control if possible, but if not just scroll such that
		# the top/left edges are still visible

		# is it past the right edge ?
		if cr.right > clntsz.width and sppu_x > 0:
			diff = (cr.right - clntsz.width) / sppu_x
			if cr.x - diff * sppu_x > 0:
				new_vs_x = vs_x + diff + 1
			else:
				new_vs_x = vs_x + (cr.x / sppu_x)
				
		# is it below the bottom ?
		if cr.bottom > clntsz.height and sppu_y > 0:
			diff = (cr.bottom - clntsz.height) / sppu_y
			if cr.y - diff * sppu_y > 0:
				new_vs_y = vs_y + diff + 1
			else:
				new_vs_y = vs_y + (cr.y / sppu_y)

		# if we need to adjust
		if new_vs_x != -1 or new_vs_y != -1:
			#print "%s: (%s, %s)" % (self.GetName(), new_vs_x, new_vs_y)
			self.Scroll(new_vs_x, new_vs_y)

wx.ScrolledWindow = ScrolledWindow


class GenButton(object):

	"""
	A generic button, based on wx.lib.buttons.GenButton.
	
	Fixes wx.lib.buttons.ThemedGenButton not taking into account backgroun
	color when pressed.
	
	"""

	def __init__(self):
		self.bezelWidth = 2
		self.hasFocus = False
		self.up = True
		self.useFocusInd = True

	def OnPaint(self, event):
		(width, height) = self.GetClientSizeTuple()
		x1 = y1 = 0
		x2 = width-1
		y2 = height-1

		dc = wx.PaintDC(self)
		brush = self.GetBackgroundBrush(dc)
		if brush is not None:
			brush.SetColour(self.BackgroundColour)
			dc.SetBackground(brush)
			dc.Clear()

		self.DrawBezel(dc, x1, y1, x2, y2)
		self.DrawLabel(dc, width, height)
		if self.hasFocus and self.useFocusInd:
			self.DrawFocusIndicator(dc, width, height)


class GenBitmapButton(GenButton, _GenBitmapButton):

	"""
	A generic bitmap button, based on wx.lib.buttons.GenBitmapButton.
	
	Fixes wx.lib.buttons.GenBitmapButton not taking into account backgroun
	color when pressed.
	
	"""

	def __init__(self, *args, **kwargs):
		GenButton.__init__(self)
		_GenBitmapButton.__init__(self, *args, **kwargs)

	@Property
	def BitmapFocus():
		def fget(self):
			return self.GetBitmapFocus()

		def fset(self, bitmap):
			self.SetBitmapFocus(self, bitmap)

		return locals()

	@Property
	def BitmapDisabled():
		def fget(self):
			return self.GetBitmapDisabled()

		def fset(self, bitmap):
			self.SetBitmapDisabled(self, bitmap)

		return locals()

	@Property
	def BitmapSelected():
		def fget(self):
			return self.GetBitmapSelected()

		def fset(self, bitmap):
			self.SetBitmapSelected(self, bitmap)

		return locals()

	@Property
	def BitmapLabel():
		def fget(self):
			return self.GetBitmapLabel()

		def fset(self, bitmap):
			self.SetBitmapLabel(self, bitmap)

		return locals()

	def DrawLabel(self, dc, width, height, dx=0, dy=0):
		bmp = self.BitmapLabel
		if self.BitmapDisabled and not self.IsEnabled():
			bmp = self.BitmapDisabled
		if self.BitmapFocus and self.hasFocus:
			bmp = self.BitmapFocus
		if self.BitmapSelected and not self.up:
			bmp = self.BitmapSelected
		bw, bh = bmp.GetWidth(), bmp.GetHeight()
		hasMask = bmp.GetMask() != None
		dc.DrawBitmap(bmp, (width-bw)/2+dx, (height-bh)/2+dy, hasMask)

	def SetBitmapLabel(self, bitmap, createOthers=True):
		"""
		Set the bitmap to display normally.
		This is the only one that is required. If
		createOthers is True, then the other bitmaps
		will be generated on the fly.  Currently,
		only the disabled bitmap is generated.
		"""
		self.bmpLabel = bitmap
		if bitmap is not None and createOthers:
			image = bitmap.ConvertToImage()

			# Disabled
			if image.HasMask():
				image.InitAlpha()
			if image.HasAlpha():
				alphabuffer = image.GetAlphaBuffer()
				for i, byte in enumerate(alphabuffer):
					if byte > "\0":
						alphabuffer[i] = chr(int(round(ord(byte) * .3)))
			self.SetBitmapDisabled(image.ConvertToBitmap())

			# Selected
			image = bitmap.ConvertToImage()
			databuffer = image.GetDataBuffer()
			for i, byte in enumerate(databuffer):
				if byte > "\0":
					databuffer[i] = chr(int(round(ord(byte) * .5)))
			self.SetBitmapSelected(image.ConvertToBitmap())


class ThemedGenButton(GenButton, _ThemedGenButton):

	"""
	A themed generic button, based on wx.lib.buttons.ThemedGenButton.

	Fixes wx.lib.buttons.ThemedGenButton sometimes not reflecting enabled
	state correctly as well as not taking into account background color when
	pressed, and mimics a default button under Windows more closely by
	not drawing a focus outline and not shifting the label when pressed.
	
	Also implements state for SetDefault.

	"""

	_reallyenabled = True
	labelDelta = 1

	def __init__(self, *args, **kwargs):
		GenButton.__init__(self)
		_ThemedGenButton.__init__(self, *args, **kwargs)
		self._default = False

	def Disable(self):
		self.Enable(False)

	def DrawBezel(self, dc, x1, y1, x2, y2):
		rect = wx.Rect(x1, y1, x2, y2)
		if self.up:
			state = 0
		else:
			state = wx.CONTROL_PRESSED | wx.CONTROL_SELECTED
		if not self.IsEnabled():
			state = wx.CONTROL_DISABLED
		elif self._default:
			state |= wx.CONTROL_ISDEFAULT
		pt = self.ScreenToClient(wx.GetMousePosition())
		if self.GetClientRect().Contains(pt):
			state |= wx.CONTROL_CURRENT
		wx.RendererNative.Get().DrawPushButton(self, dc, rect, state)

	def DrawLabel(self, dc, width, height, dx=0, dy=0):
		dc.SetFont(self.GetFont())
		if self.Enabled:
			dc.SetTextForeground(self.ForegroundColour)
		else:
			dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
		label = self.Label
		tw, th = dc.GetTextExtent(label)
		if sys.platform != "win32" and not self.up:
			dx = dy = self.labelDelta
		dc.DrawText(label, (width-tw)/2+dx, (height-th)/2+dy)

	def Enable(self, enable=True):
		if enable != self.Enabled:
			self.Enabled = enable
			wx.PyControl.Enable(self, enable)
			self.Refresh()

	@Property
	def Enabled():
		def fget(self):
			return self._reallyenabled
		
		def fset(self, enabled):
			self._reallyenabled = enabled
		
		return locals()

	def IsEnabled(self):
		return self.Enabled

	def OnLeftDown(self, event):
		if not self.Enabled:
			return
		self.up = False
		self.CaptureMouse()
		self.SetFocus()
		self.useFocusInd = False
		self.Refresh()
		event.Skip()

	def OnGainFocus(self, event):
		self.hasFocus = True
		self.useFocusInd = bool(self.bezelWidth)
		self.Refresh()
		self.Update()

	def SetDefault(self):
		self._default = True
		_ThemedGenButton.SetDefault(self)
