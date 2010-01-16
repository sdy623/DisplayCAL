#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from wxfixes import wx

def GetAllChildren(self):
	""" Get children of window and its subwindows """
	children = self.GetChildren()
	allchildren = []
	for child in children:
		allchildren += [child]
		if hasattr(child, "GetAllChildren") and hasattr(child.GetAllChildren, 
														"__call__"):
			allchildren += child.GetAllChildren()
	return allchildren

wx.Window.GetAllChildren = GetAllChildren


def GetDisplay(self):
	""" Return the display the window is shown on """
	display_no = wx.Display.GetFromWindow(self)
	if display_no < 0: # window outside visible area
		display_no = 0
	return wx.Display(display_no)

wx.Window.GetDisplay = GetDisplay


def SetMaxFontSize(self, pointsize=11):
	font = self.GetFont()
	if font.GetPointSize() > pointsize:
		font.SetPointSize(pointsize)
		self.SetFont(font)

wx.Window.SetMaxFontSize = SetMaxFontSize


def SetSaneGeometry(self, x=None, y=None, w=None, h=None):
	"""
	Set a 'sane' window position and/or size (within visible screen area).
	"""
	if not None in (x, y):
		# First, move to coordinates given
		self.SetPosition((x, y))
	# Returns the first display's client area if the window 
	# is completely outside the client area of all displays
	display_client_rect = self.GetDisplay().ClientArea 
	if sys.platform not in ("darwin", "win32"): # Linux
		safety_margin = 45
	else:
		safety_margin = 20
	if not None in (w, h):
		# Set given size, but resize if needed to fit inside client area
		self.SetSize((min(display_client_rect[2] - safety_margin, w), 
			min(display_client_rect[3] - safety_margin, h))) 
	if not None in (x, y):
		if not display_client_rect.ContainsXY(x, y) or \
		   not display_client_rect.ContainsRect((x, y, 100, 100)):
			# If outside client area or near the borders,
			# move to leftmost / topmost coordinates of client area
			self.SetPosition(display_client_rect[0:2])

wx.Window.SetSaneGeometry = SetSaneGeometry


def GridGetSelectedRowsFromSelection(self):
	"""
	Return the number of fully selected rows.
	
	Unlike GetSelectedRows, include rows that have been selected
	by chosing individual cells.
	
	"""
	sel = self.GetSelection()
	numcols = self.GetNumberCols()
	rows = []
	i = -1
	for cell in sel:
		row, col = cell
		if row > i:
			i = row
			rownumcols = 0
		rownumcols += 1
		if rownumcols == numcols:
			rows += [row]
	return rows

wx.grid.Grid.GetSelectedRowsFromSelection = GridGetSelectedRowsFromSelection


def GridGetSelectionRows(self):
	"""
	Return the selected rows, even if not all cells in a row are selected.
	"""
	sel = self.GetSelection()
	rows = []
	i = -1
	for cell in sel:
		row, col = cell
		if row > i:
			i = row
			rows += [row]
	return rows

wx.grid.Grid.GetSelectionRows = GridGetSelectionRows


def IsSizer(self):
	""" Check if the window is a sizer """
	return isinstance(self, wx.Sizer)

wx.Window.IsSizer = IsSizer


class CustomEvent(wx.PyEvent):

	def __init__(self, typeId, object, window=None):
		wx.PyEvent.__init__(self, typeId, object.GetId())
		self.evtType = [typeId]
		self.typeId = typeId
		self.object = object
		self.window = window

	def GetEventObject(self):
		return self.object

	def GetEventType(self):
		return self.typeId

	def GetWindow(self):
		return self.window


class CustomGridCellEvent(CustomEvent):
	def __init__(self, typeId, object, row=-1, col=-1, window=None):
		CustomEvent.__init__(self, typeId, object, window)
		self.row = row
		self.col = col

	def GetRow(self):
		return self.row

	def GetCol(self):
		return self.col


class FileDrop(wx.FileDropTarget):

	def __init__(self, drophandlers=None):
		wx.FileDropTarget.__init__(self)
		if drophandlers is None:
			drophandlers = {}
		self.drophandlers = drophandlers
		self.unsupported_handler = None

	def OnDropFiles(self, x, y, filenames):
		self._files = {}
		self._filenames = filenames

		for filename in filenames:
			name, ext = os.path.splitext(filename)
			if ext.lower() in self.drophandlers:
				self._files[ext.lower()] = filename

		if len(self._files):
			for key in self._files:
				self.drophandlers[key](self._files[key])
		elif self.unsupported_handler:
			self.unsupported_handler()
