# -*- coding: utf-8 -*-

import re
import subprocess as sp
import math
import os
import sys
import tempfile

from config import (defaults, fs_enc, get_argyll_display_number, get_data_path,
					get_display_profile, get_display_rects, getbitmap, getcfg,
					geticon, profile_ext, setcfg, writecfg)
from log import safe_print
from meta import name as appname
from options import debug
from ordereddict import OrderedDict
from util_os import launch_file
from util_str import safe_unicode, universal_newlines, wrap
from worker import (Error, check_set_argyll_bin, get_argyll_util,
					make_argyll_compatible_path, show_result_dialog)
from wxaddons import get_platform_window_decoration_size, wx
from wxLUTViewer import LUTCanvas, LUTFrame
from wxVRML2X3D import vrmlfile2x3dhtmlfile
from wxwindows import (BitmapBackgroundPanelText, FileDrop, InfoDialog,
					   SimpleBook, TwoWaySplitter)
import colormath
import config
import wxenhancedplot as plot
import localization as lang
import ICCProfile as ICCP

BGCOLOUR = "#333333"
FGCOLOUR = "#999999"
TEXTCOLOUR = "#333333"

if sys.platform == "darwin":
	FONTSIZE_LARGE = 11
	FONTSIZE_MEDIUM = 11
	FONTSIZE_SMALL = 10
else:
	FONTSIZE_LARGE = 10
	FONTSIZE_MEDIUM = 8
	FONTSIZE_SMALL = 8


class GamutCanvas(LUTCanvas):

	def __init__(self, *args, **kwargs):
		LUTCanvas.__init__(self, *args, **kwargs)
		self.SetEnableTitle(False)
		self.SetFontSizeAxis(FONTSIZE_SMALL)
		self.SetFontSizeLegend(FONTSIZE_SMALL)
		self.pcs_data = []
		self.profiles = {}
		self.colorspace = "a*b*"
		self.intent = ""
		self.direction = ""
		self.order = ""
		self.reset()
		self.resetzoom()

	def DrawCanvas(self, title=None, colorspace=None, whitepoint=None,
				   center=False, show_outline=True):
		if not title:
			title = ""
		if colorspace:
			self.colorspace = colorspace
		
		# Defaults
		poly = plot.PolyLine
		poly._attributes["width"] = 3
		polys = []

		# Very rough (in a*b*)
		optimalcolors = [(102, -131),
						 (119, -134),
						 (128, -133),
						 (127, -123),
						 (124, -118),
						 (114, -108),
						 (115, -94),
						 (116, -77),
						 (114, -63),
						 (110, -46),
						 (104, -27),
						 (97, -1),
						 (92, 32),
						 (90, 53),
						 (89, 73),
						 (88, 90),
						 (84, 102),
						 (75, 114),
						 (64, 124),
						 (50, 133),
						 (35, 141),
						 (17, 145),
						 (-6, 140),
						 (-46, 129),
						 (-81, 116),
						 (-113, 97),
						 (-144, 68),
						 (-160, 39),
						 (-163, 26),
						 (-162, 16),
						 (-155, 4),
						 (-135, -12),
						 (-89, -46),
						 (-58, -67),
						 (-29, -83),
						 (17, -103),
						 (67, -121),
						 (102, -131)]

		if self.colorspace == "xy":
			self.spec_x = 8
			self.spec_y = 8
			label_x = "x"
			label_y = "y"
			if show_outline:
				polys.append(plot.PolySpline([(0.173, 0.003),
											  (0.165, 0.010),
											  (0.157, 0.017),
											  (0.144, 0.029),
											  (0.135, 0.039),
											  (0.124, 0.057),
											  (0.109, 0.086),
											  (0.090, 0.131),
											  (0.068, 0.200),
											  (0.045, 0.295),
											  (0.023, 0.413),
											  (0.007, 0.538),
											  (0.003, 0.655),
											  (0.013, 0.750),
											  (0.039, 0.814),
											  (0.074, 0.835),
											  (0.115, 0.827),
											  (0.156, 0.807),
											  (0.194, 0.783),
											  (0.230, 0.755),
											  (0.266, 0.725),
											  (0.303, 0.693),
											  (0.338, 0.660),
											  (0.374, 0.626),
											  (0.513, 0.488),
											  (0.740, 0.260)],
											 colour=wx.Colour(102, 102, 102, 153),
											 width=1.75))
				polys.append(plot.PolyLine([(0.173, 0.003), (0.740, 0.260)],
										   colour=wx.Colour(102, 102, 102, 153),
										   width=1.75))
			max_x = 0.84
			max_y = 0.84
			min_x = 0
			min_y = 0
			step = .1
		elif self.colorspace == "u'v'":
			self.spec_x = 6
			self.spec_y = 6
			label_x = "u'"
			label_y = "v'"
			if show_outline:
				polys.append(plot.PolySpline([(0.260, 0.018),
											  (0.254, 0.016),
											  (0.232, 0.038),
											  (0.213, 0.059),
											  (0.186, 0.090),
											  (0.142, 0.154),
											  (0.082, 0.272),
											  (0.028, 0.410),
											  (0.005, 0.501),
											  (0.001, 0.543),
											  (0.002, 0.559),
											  (0.006, 0.570),
											  (0.012, 0.577),
											  (0.021, 0.583),
											  (0.036, 0.586),
											  (0.052, 0.587),
											  (0.081, 0.586),
											  (0.115, 0.582),
											  (0.156, 0.577),
											  (0.207, 0.569),
											  (0.264, 0.561),
											  (0.334, 0.550),
											  (0.408, 0.539),
											  (0.472, 0.530),
											  (0.624, 0.507)],
											 colour=wx.Colour(102, 102, 102, 153),
											 width=1.75))
				polys.append(plot.PolyLine([(0.260, 0.018), (0.624, 0.507)],
										   colour=wx.Colour(102, 102, 102, 153),
										   width=1.75))
			max_x = 0.6
			max_y = 0.6
			min_x = 0
			min_y = 0
			step = .1
		elif self.colorspace == "u*v*":
			# Not used, hard to present gamut projection appropriately in 2D
			# because blue tones 'cave in' towards the center
			self.spec_x = 8
			self.spec_y = 8
			label_x = "u*"
			label_y = "v*"
			max_x = 50.0
			max_y = 50.0
			min_x = -50.0
			min_y = -50.0
			step = 50
		elif self.colorspace == "DIN99":
			self.spec_x = 8
			self.spec_y = 8
			label_x = "a99"
			label_y = "b99"
			max_x = 50.0
			max_y = 50.0
			min_x = -50.0
			min_y = -50.0
			step = 25
		elif self.colorspace in ("DIN99b", "DIN99c", "DIN99d"):
			self.spec_x = 8
			self.spec_y = 8
			if self.colorspace == "DIN99c":
				label_x = "a99c"
				label_y = "b99c"
			else:
				label_x = "a99d"
				label_y = "b99d"
			max_x = 65.0
			max_y = 65.0
			min_x = -65.0
			min_y = -65.0
			step = 25
		else:
			self.spec_x = 8
			self.spec_y = 8
			label_x = "a*"
			label_y = "b*"
			max_x = 130.0
			max_y = 146.0
			min_x = -166.0
			min_y = -136.0
			step = 50
		
		convert2coords = {"a*b*": lambda X, Y, Z: colormath.XYZ2Lab(*[v * 100 for v in X, Y, Z])[1:],
						  "xy": lambda X, Y, Z: colormath.XYZ2xyY(X, Y, Z)[:2],
						  "u*v*": lambda X, Y, Z: colormath.XYZ2Luv(*[v * 100 for v in X, Y, Z])[1:],
						  "u'v'": lambda X, Y, Z: colormath.XYZ2Lu_v_(X, Y, Z)[1:],
						  "DIN99": lambda X, Y, Z: colormath.XYZ2DIN99(*[v * 100 for v in X, Y, Z])[1:],
						  "DIN99b": lambda X, Y, Z: colormath.XYZ2DIN99b(*[v * 100 for v in X, Y, Z])[1:],
						  "DIN99c": lambda X, Y, Z: colormath.XYZ2DIN99c(*[v * 100 for v in X, Y, Z])[1:],
						  "DIN99d": lambda X, Y, Z: colormath.XYZ2DIN99d(*[v * 100 for v in X, Y, Z])[1:]}[self.colorspace]

		if show_outline and self.colorspace in ("a*b*", "DIN99", "DIN99b",
												"DIN99c", "DIN99d"):
			polys.append(plot.PolySpline([convert2coords(*colormath.Lab2XYZ(0, a, b))
										  for a, b in optimalcolors],
										 colour=wx.Colour(102, 102, 102, 153),
										 width=1.75))
		
		# Add color temp graph from 4000 to 9000K
		if whitepoint == 1:
			colortemps = []
			for kelvin in xrange(4000, 25001, 100):
				colortemps.append(convert2coords(*colormath.CIEDCCT2XYZ(kelvin)))
			polys.append(plot.PolySpline(colortemps,
										 colour=wx.Colour(255, 255, 255, 204),
										 width=1.5))
		elif whitepoint == 2:
			colortemps = []
			for kelvin in xrange(1667, 25001, 100):
				colortemps.append(convert2coords(*colormath.planckianCT2XYZ(kelvin)))
			polys.append(plot.PolySpline(colortemps,
										 colour=wx.Colour(255, 255, 255, 204),
										 width=1.5))

		kwargs = {"scale": 255}

		amount = len(self.pcs_data)

		for i, pcs_triplets in enumerate(reversed(self.pcs_data)):
			if not pcs_triplets or len(pcs_triplets) == 1:
				amount -= 1
				continue

			# Convert xicclu output to coordinates
			coords = []
			for pcs_triplet in pcs_triplets:
				coords.append(convert2coords(*pcs_triplet))

			profile = self.profiles.get(len(self.pcs_data) - 1 - i)
			if (profile and profile.profileClass == "nmcl" and
				"ncl2" in profile.tags and
				isinstance(profile.tags.ncl2,
						   ICCP.NamedColor2Type) and
				profile.connectionColorSpace in ("Lab", "XYZ")):
				# Named color profile
				for j, (x, y) in enumerate(coords):
					RGBA = colormath.XYZ2RGB(*pcs_triplets[j],
											 **kwargs)
					polys.append(plot.PolyMarker([(x, y)],
												 colour=wx.Colour(*RGBA),
												 size=2,
												 marker="plus",
												 width=1.75))
			else:
				xy = []
				for x, y in coords[:-1]:
					xy.append((x, y))
					if i == 0 or amount == 1:
						if x > max_x:
							max_x = x
						if y > max_y:
							max_y = y
						if x < min_x:
							min_x = x
						if y < min_y:
							min_y = y

				xy2 = []
				for j, (x, y) in enumerate(xy):
					xy2.append((x, y))
					if len(xy2) == self.size:
						xy3 = []
						for k, (x, y) in enumerate(xy2):
							xy3.append((x, y))
							if len(xy3) == 2:
								if i == 1:
									# Draw comparison profile with grey outline
									RGBA = 102, 102, 102, 255
									w = 2
								else:
									RGBA = colormath.XYZ2RGB(*pcs_triplets[j -
																		   len(xy2) + k],
															 **kwargs)
									w = 3
								polys.append(poly(list(xy3),
												  colour=wx.Colour(*RGBA),
												  width=w))
								if i == 1:
									xy3 = []
								else:
									xy3 = xy3[1:]
						xy2 = xy2[self.size:]
			
			# Add whitepoint
			x, y = coords[-1]
			if i == 1:
				# Draw comparison profile with grey outline
				RGBA = 204, 204, 204, 102
				marker="cross"
				s = 1.5
				w = 1.75
			else:
				RGBA = colormath.XYZ2RGB(*pcs_triplets[-1], **kwargs)
				marker = "plus"
				s = 2
				w = 1.75
			polys.append(plot.PolyMarker([(x, y)],
										 colour=wx.Colour(*RGBA),
										 size=s,
										 marker=marker,
										 width=w))
		
		max_abs_x = max(abs(min_x), max_x)
		max_abs_y = max(abs(min_y), max_y)

		if center:
			self.axis_x = self.axis_y = (min(min_x, min_y), max(max_x, max_y))
			self.center_x = 0 + (min_x + max_x) / 2
			self.center_y = 0 + (min_y + max_y) / 2
		self.ratio = [max(max_abs_x, max_abs_y) /
					  max(max_abs_x, max_abs_y)] * 2
		if colorspace == "ab" or colorspace.startswith("DIN99"):
			ab_range = max(abs(min_x), abs(min_y)) + max(max_x, max_y)
			self.spec_x = ab_range / step
			self.spec_y = ab_range / step

		if polys:
			self._DrawCanvas(plot.PlotGraphics(polys, title, label_x, label_y))
	
	def reset(self):
		self.axis_x = self.axis_y = -128, 128
		self.ratio = 1.0, 1.0

	def set_pcs_data(self, i):
		if len(self.pcs_data) < i + 1:
			self.pcs_data.append([])
		else:
			self.pcs_data[i] = []
	
	def setup(self, profiles=None, profile_no=None, intent="a", direction="f",
			  order="n"):
		self.size = 40  # Number of segments from one primary to the next secondary color
		
		if not check_set_argyll_bin():
			return
		
		# Setup xicclu
		xicclu = get_argyll_util("xicclu")
		if not xicclu:
			return
		cwd = self.worker.create_tempdir()
		if isinstance(cwd, Exception):
			raise cwd
		
		if not profiles:
			profiles = [ICCP.ICCProfile(get_data_path("ref/sRGB.icm")),
						get_display_profile()]
		for i, profile in enumerate(profiles):
			if profile_no is not None and i != profile_no:
				continue

			if not profile or profile.profileClass == "link":
				self.set_pcs_data(i)
				self.profiles[i] = None
				continue

			id = profile.calculateID(False)
			check = self.profiles.get(i)
			if (check and check.ID == id and intent == self.intent and
				direction == self.direction and order == self.order):
				continue

			self.profiles[i] = profile

			self.set_pcs_data(i)

			pcs_triplets = []
			if (profile.profileClass == "nmcl" and "ncl2" in profile.tags and
				isinstance(profile.tags.ncl2, ICCP.NamedColor2Type) and
				profile.connectionColorSpace in ("Lab", "XYZ")):
				for k, v in profile.tags.ncl2.iteritems():
					color = v.pcs.values()
					if profile.connectionColorSpace == "Lab":
						# Need to convert to XYZ
						color = colormath.Lab2XYZ(*color)
					if intent == "a" and "wtpt" in profile.tags:
						color = colormath.adapt(color[0], color[1], color[2],
												whitepoint_destination=profile.tags.wtpt.ir.values())
					pcs_triplets.append(color)
				pcs_triplets.sort()
			elif profile.version >= 4:
				self.profiles[i] = None
				self.errors.append(Error("\n".join([lang.getstr("profile.iccv4.unsupported"),
													profile.getDescription()])))
				continue
			else:
				channels = {'XYZ': 3,
							'Lab': 3,
							'Luv': 3,
							'YCbr': 3,
							'Yxy': 3,
							'RGB': 3,
							'GRAY': 1,
							'HSV': 3,
							'HLS': 3,
							'CMYK': 4,
							'CMY': 3,
							'2CLR': 2,
							'3CLR': 3,
							'4CLR': 4,
							'5CLR': 5,
							'6CLR': 6,
							'7CLR': 7,
							'8CLR': 8,
							'9CLR': 9,
							'ACLR': 10,
							'BCLR': 11,
							'CCLR': 12,
							'DCLR': 13,
							'ECLR': 14,
							'FCLR': 15}.get(profile.colorSpace)

				if not channels:
					self.errors.append(Error(lang.getstr("profile.unsupported",
														 (profile.profileClass,
														  profile.colorSpace))))
					continue

				# Create input values
				device_values = []
				if profile.colorSpace in ("Lab", "Luv", "XYZ", "Yxy"):
					# Use ICC PCSXYZ encoding range
					minv = 0.0
					maxv = 0xffff / 32768.0
				else:
					minv = 0.0
					maxv = 1.0
				step = (maxv - minv) / (self.size - 1)
				for j in xrange(min(3, channels)):
					for k in xrange(min(3, channels)):
						device_value = [0.0] * channels
						device_value[j] = maxv
						if j != k or channels == 1:
							for l in xrange(self.size):
								device_value[k] = minv + step * l
								device_values.append(list(device_value))
				if profile.colorSpace in ("HLS", "HSV", "Lab", "Luv", "YCbr", "Yxy"):
					# Convert to actual color space
					# TODO: Handle HLS and YCbr
					tmp = list(device_values)
					device_values = []
					for j, values in enumerate(tmp):
						if profile.colorSpace == "HSV":
							HSV = list(colormath.RGB2HSV(*values))
							device_values.append(HSV)
						elif profile.colorSpace == "Lab":
							Lab = list(colormath.XYZ2Lab(*[v * 100
														   for v in values]))
							device_values.append(Lab)
						elif profile.colorSpace == "Luv":
							Luv = list(colormath.XYZ2Luv(*[v * 100
														   for v in values]))
							device_values.append(Luv)
						elif profile.colorSpace == "Yxy":
							xyY = list(colormath.XYZ2xyY(*values))
							device_values.append(xyY)
				
				# Add white
				if profile.colorSpace == "RGB":
					device_values.append([1.0] * channels)
				elif profile.colorSpace == "HLS":
					device_values.append([0, 1, 0])
				elif profile.colorSpace == "HSV":
					device_values.append([0, 0, 1])
				elif profile.colorSpace in ("Lab", "Luv", "YCbr"):
					if profile.colorSpace == "YCbr":
						device_values.append([1.0, 0.0, 0.0])
					else:
						device_values.append([100.0, 0.0, 0.0])
				elif profile.colorSpace in ("XYZ", "Yxy"):
					if profile.colorSpace == "XYZ":
						device_values.append(profile.tags.wtpt.pcs.values())
					else:
						device_values.append(profile.tags.wtpt.pcs.xyY)
				elif profile.colorSpace != "GRAY":
					device_values.append([0.0] * channels)

				if debug:
					safe_print("In:")
					for v in device_values:
						safe_print(" ".join(("%3.4f", ) * len(v)) % tuple(v))

				# Lookup device -> XYZ values through profile using xicclu
				try:
					odata = self.worker.xicclu(profile, device_values, intent,
											   direction, order)
				except Exception, exception:
					self.errors.append(Error(safe_unicode(exception)))
					continue

				if debug:
					safe_print("Out:")
				for pcs_triplet in odata:
					if debug:
						safe_print(" ".join(("%3.4f", ) * len(pcs_triplet)) % tuple(pcs_triplet))
					pcs_triplets.append(pcs_triplet)
					if profile.connectionColorSpace == "Lab":
						pcs_triplets[-1] = list(colormath.Lab2XYZ(*pcs_triplets[-1]))

			if len(self.pcs_data) < i + 1:
				self.pcs_data.append(pcs_triplets)
			else:
				self.pcs_data[i] = pcs_triplets
		
		# Remove temporary files
		self.worker.wrapup(False)
		
		self.intent = intent
		self.direction = direction
		self.order = order


class GamutViewOptions(wx.Panel):
	
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.SetBackgroundColour(BGCOLOUR)
		self.sizer = wx.FlexGridSizer(0, 3, 4)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(2)
		self.SetSizer(self.sizer)

		self.sizer.Add((0, 0))
		legendsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer.Add(legendsizer)
		
		# Whitepoint legend
		legendsizer.Add(wx.StaticBitmap(self, -1,
											   getbitmap("theme/cross-2px-12x12-fff")),
							   flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
							   border=2)
		self.whitepoint_legend = wx.StaticText(self, -1,
											   lang.getstr("whitepoint"))
		self.whitepoint_legend.SetMaxFontSize(11)
		self.whitepoint_legend.SetForegroundColour(FGCOLOUR)
		legendsizer.Add(self.whitepoint_legend,
							 flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
							 border=10)
		
		# Comparison profile whitepoint legend
		self.comparison_whitepoint_bmp = wx.StaticBitmap(self, -1,
														 getbitmap("theme/x-2px-12x12-999"))
		legendsizer.Add(self.comparison_whitepoint_bmp,
						flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
							 border=20)
		self.comparison_whitepoint_legend = wx.StaticText(self, -1,
														  "%s (%s)" % (lang.getstr("whitepoint"),
																	   lang.getstr("comparison_profile")))
		self.comparison_whitepoint_legend.SetMaxFontSize(11)
		self.comparison_whitepoint_legend.SetForegroundColour(FGCOLOUR)
		legendsizer.Add(self.comparison_whitepoint_legend,
						flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
		self.sizer.Add((0, 0))
		
		# Empty 'row'
		self.sizer.Add((0, 0))
		self.sizer.Add((0, 0))
		self.sizer.Add((0, 0))
		
		self.sizer.Add((0, 0))
		self.options_sizer = wx.FlexGridSizer(0, 3, 4, 8)
		self.sizer.Add(self.options_sizer)
		
		# Colorspace select
		self.colorspace_outline_bmp = wx.StaticBitmap(self, -1,
													  getbitmap("theme/solid-16x2-666"))
		self.options_sizer.Add(self.colorspace_outline_bmp,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.colorspace_label = wx.StaticText(self, -1,
											  lang.getstr("colorspace"))
		self.colorspace_label.SetMaxFontSize(11)
		self.colorspace_label.SetForegroundColour(FGCOLOUR)
		self.options_sizer.Add(self.colorspace_label,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.colorspace_select = wx.Choice(self, -1,
												 size=(150, -1), 
												 choices=["CIE a*b*",
														  #"CIE u*v*",
														  "CIE u'v'",
														  "CIE xy",
														  "DIN99",
														  "DIN99b",
														  "DIN99c",
														  "DIN99d"])
		self.options_sizer.Add(self.colorspace_select, 
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.colorspace_select.Bind(wx.EVT_CHOICE, self.generic_select_handler)
		self.colorspace_select.SetSelection(0)
		
		# Colorspace outline
		self.options_sizer.Add((0, 0))
		self.options_sizer.Add((0, 0))
		self.draw_gamut_outline_cb = wx.CheckBox(self, -1,
												 lang.getstr("colorspace.show_outline"))
		self.draw_gamut_outline_cb.Bind(wx.EVT_CHECKBOX,
										self.draw_gamut_outline_handler)
		self.draw_gamut_outline_cb.SetMaxFontSize(11)
		self.draw_gamut_outline_cb.SetForegroundColour(FGCOLOUR)
		self.draw_gamut_outline_cb.SetValue(True)
		self.options_sizer.Add(self.draw_gamut_outline_cb,
							   flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
							   border=4)
		
		# Colortemperature curve select
		self.whitepoint_bmp = wx.StaticBitmap(self, -1,
											  getbitmap("theme/solid-16x1-fff"))
		self.options_sizer.Add(self.whitepoint_bmp,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.whitepoint_label = wx.StaticText(self, -1,
										 lang.getstr("whitepoint.colortemp.locus.curve"))
		self.whitepoint_label.SetMaxFontSize(11)
		self.whitepoint_label.SetForegroundColour(FGCOLOUR)
		self.options_sizer.Add(self.whitepoint_label,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.whitepoint_select = wx.Choice(self, -1,
												 size=(150, -1), 
												 choices=[lang.getstr("calibration.file.none"),
														  lang.getstr("whitepoint.colortemp.locus.daylight"),
														  lang.getstr("whitepoint.colortemp.locus.blackbody")])
		self.options_sizer.Add(self.whitepoint_select, 
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.whitepoint_select.Bind(wx.EVT_CHOICE, self.generic_select_handler)
		self.whitepoint_select.SetSelection(0)
		self.whitepoint_bmp.Hide()
		
		# Comparison profile select
		self.comparison_profile_bmp = wx.StaticBitmap(self, -1,
													  getbitmap("theme/dashed-16x2-666"))
		self.options_sizer.Add(self.comparison_profile_bmp,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.comparison_profile_label = wx.StaticText(self, -1,
													  lang.getstr("comparison_profile"))
		self.comparison_profile_label.SetMaxFontSize(11)
		self.comparison_profile_label.SetForegroundColour(FGCOLOUR)
		self.options_sizer.Add(self.comparison_profile_label,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.comparison_profiles = OrderedDict([(lang.getstr("calibration.file.none"),
												 None)])
		for name in ["sRGB", "ClayRGB1998", "ProPhoto", "Rec601_525_60",
					 "Rec601_625_50", "Rec709", "SMPTE240M", "SMPTE431_P3"]:
			path = get_data_path("ref/%s.icm" % name)
			if path:
				profile = ICCP.ICCProfile(path)
				self.comparison_profiles[profile.getDescription()] = profile
		for path in ["AdobeRGB1998.icc",
					 "ECI-RGB.V1.0.icc",
					 "eciRGB_v2.icc",
					 "GRACoL2006_Coated1v2.icc",
					 "ISOcoated.icc",
					 "ISOcoated_v2_eci.icc",
					 #"ISOnewspaper26v4.icc",
					 #"ISOuncoated.icc",
					 #"ISOuncoatedyellowish.icc",
					 "ISOwebcoated.icc",
					 "LStar-RGB.icc",
					 "LStar-RGB-v2.icc",
					 "PSO_Coated_300_NPscreen_ISO12647_eci.icc",
					 "PSO_Coated_NPscreen_ISO12647_eci.icc",
					 "PSO_LWC_Improved_eci.icc",
					 "PSO_LWC_Standard_eci.icc",
					 "PSO_MFC_Paper_eci.icc",
					 #"PSO_Uncoated_ISO12647_eci.icc",
					 #"PSO_Uncoated_NPscreen_ISO12647_eci.icc",
					 #"PSO_SNP_Paper_eci.icc",
					 "SC_paper_eci.icc",
					 "SWOP2006_Coated3v2.icc",
					 "SWOP2006_Coated5v2.icc"]:
			try:
				profile = ICCP.ICCProfile(path)
			except IOError:
				pass
			else:
				self.comparison_profiles[profile.getDescription()] = profile
		comparison_profiles = self.comparison_profiles[2:]
		def cmp(x, y):
			if x.lower() > y.lower():
				return 1
			if x.lower() < y.lower():
				return -1
			return 0
		comparison_profiles.sort(cmp)
		self.comparison_profiles = self.comparison_profiles[:2]
		self.comparison_profiles.update(comparison_profiles)
		self.comparison_profile_select = wx.Choice(self, -1,
												   size=(150, -1), 
												   choices=self.comparison_profiles.keys()[:2] +
														   comparison_profiles.keys())
		self.options_sizer.Add(self.comparison_profile_select, 
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.comparison_profile_select.Bind(wx.EVT_CHOICE,
											self.comparison_profile_select_handler)
		self.comparison_profile_select.SetSelection(1)
		
		# Rendering intent select
		self.options_sizer.Add((0, 0))
		self.rendering_intent_label = wx.StaticText(self, -1,
													lang.getstr("rendering_intent"))
		self.rendering_intent_label.SetMaxFontSize(11)
		self.rendering_intent_label.SetForegroundColour(FGCOLOUR)
		self.options_sizer.Add(self.rendering_intent_label,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.rendering_intent_select = wx.Choice(self, -1,
												 size=(150, -1), 
												 choices=[lang.getstr("gamap.intents.a"),
														  lang.getstr("gamap.intents.r"),
														  lang.getstr("gamap.intents.p"),
														  lang.getstr("gamap.intents.s")])
		self.options_sizer.Add(self.rendering_intent_select, 
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.rendering_intent_select.Bind(wx.EVT_CHOICE,
										  self.rendering_intent_select_handler)
		self.rendering_intent_select.SetSelection(0)
		
		self.options_sizer.Add((0, 0))
		
		# LUT toggle
		self.toggle_clut = wx.CheckBox(self, -1, "LUT")
		self.toggle_clut.SetForegroundColour(FGCOLOUR)
		self.toggle_clut.SetMaxFontSize(11)
		self.options_sizer.Add(self.toggle_clut, flag=wx.ALIGN_CENTER_VERTICAL)
		self.toggle_clut.Bind(wx.EVT_CHECKBOX, self.toggle_clut_handler)
		
		# Direction selection
		self.direction_select = wx.Choice(self, -1,
										  size=(150, -1),
										  choices=[lang.getstr("direction.forward"),
												   lang.getstr("direction.backward.inverted")])
		self.options_sizer.Add(self.direction_select,
							   flag=wx.ALIGN_CENTER_VERTICAL)
		self.direction_select.Bind(wx.EVT_CHOICE, self.direction_select_handler)
		self.direction_select.SetSelection(0)

		self.sizer.Add((0, 0))

	def DrawCanvas(self, profile_no=None, reset=True):
		# Gamut plot
		parent = self.Parent.Parent.Parent.Parent
		parent.client.SetEnableCenterLines(False)
		parent.client.SetEnableDiagonals(False)
		parent.client.SetEnableGrid(True)
		parent.client.SetEnablePointLabel(False)
		if self.direction_select.IsShown():
			direction = {0: "f",
						 1: "ib"}.get(self.direction_select.GetSelection())
		else:
			direction = "f"
		order = {True: "n",
				 False: "r"}.get(("B2A0" in parent.profile.tags or
								  "A2B0" in parent.profile.tags) and
								 self.toggle_clut.GetValue())
		try:
			parent.client.setup([self.comparison_profiles.values()[self.comparison_profile_select.GetSelection()],
								 parent.profile],
								profile_no,
								intent={0: "a",
										1: "r",
										2: "p",
										3: "s"}.get(self.rendering_intent_select.GetSelection()),
								direction=direction, order=order)
		except Exception, exception:
			show_result_dialog(exception, parent)
		if reset:
			parent.client.reset()
			parent.client.resetzoom()
		wx.CallAfter(self.draw, center=reset)
		wx.CallAfter(parent.handle_errors)
	
	def comparison_profile_select_handler(self, event):
		self.comparison_whitepoint_bmp.Show(self.comparison_profile_select.GetSelection() > 0)
		self.comparison_whitepoint_legend.Show(self.comparison_profile_select.GetSelection() > 0)
		self.comparison_profile_bmp.Show(self.comparison_profile_select.GetSelection() > 0)
		self.DrawCanvas(0, reset=False)

	def draw(self, center=False):
		colorspace = {0: "a*b*",
					  1: "u'v'",
					  2: "xy",
					  3: "DIN99",
					  4: "DIN99b",
					  5: "DIN99c",
					  6: "DIN99d"}.get(self.colorspace_select.GetSelection(),
								   "a*b*")
		parent = self.Parent.Parent.Parent.Parent
		parent.client.proportional = True
		parent.client.DrawCanvas("%s %s" % (colorspace,
											lang.getstr("colorspace")),
								 colorspace,
								 whitepoint=self.whitepoint_select.GetSelection(),
								 center=center,
								 show_outline=self.draw_gamut_outline_cb.GetValue())
	
	def draw_gamut_outline_handler(self, event):
		self.colorspace_outline_bmp.Show(self.draw_gamut_outline_cb.GetValue())
		self.draw()
	
	def generic_select_handler(self, event):
		self.whitepoint_bmp.Show(self.whitepoint_select.GetSelection() > 0)
		parent = self.Parent.Parent.Parent.Parent
		if parent.client.profiles:
			self.draw(center=event.GetId() == self.colorspace_select.GetId())
		else:
			self.DrawCanvas()

	def rendering_intent_select_handler(self, event):
		self.DrawCanvas(reset=False)

	def direction_select_handler(self, event):
		self.DrawCanvas(reset=False)

	def toggle_clut_handler(self, event):
		parent = self.Parent.Parent.Parent.Parent
		self.Freeze()
		self.direction_select.Show("B2A0" in parent.profile.tags and
								   "A2B0" in parent.profile.tags and
								   self.toggle_clut.GetValue())
		self.DrawCanvas(reset=False)
		self.Thaw()


class ProfileInfoFrame(LUTFrame):

	def __init__(self, *args, **kwargs):
	
		if len(args) < 3 and not "title" in kwargs:
			kwargs["title"] = lang.getstr("profile.info")
		
		wx.Frame.__init__(self, *args, **kwargs)
		
		self.SetIcons(config.get_icon_bundle([256, 48, 32, 16],
											 appname + "-profile-info"))
		
		self.CreateStatusBar(1)
		
		self.profile = None
		self.xLabel = lang.getstr("in")
		self.yLabel = lang.getstr("out")
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(self.sizer)
		
		self.title_panel = BitmapBackgroundPanelText(self)
		self.title_panel.SetForegroundColour(TEXTCOLOUR)
		self.title_panel.SetBitmap(getbitmap("theme/gradient"))
		self.sizer.Add(self.title_panel, flag=wx.EXPAND)
		
		self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.title_panel.SetSizer(self.title_sizer)
		
		self.title_txt = self.title_panel
		font = wx.Font(FONTSIZE_LARGE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
					   wx.FONTWEIGHT_NORMAL)
		self.title_txt.SetFont(font)
		self.title_sizer.Add((0, 32))
		
		gridbgcolor = wx.Colour(234, 234, 234)
		
		self.splitter = TwoWaySplitter(self, -1, agwStyle = wx.SP_LIVE_UPDATE | wx.SP_NOSASH)
		self.splitter.SetBackgroundColour(wx.Colour(204, 204, 204))
		self.sizer.Add(self.splitter, 1, flag=wx.EXPAND)
		
		p1 = wx.Panel(self.splitter)
		p1.SetBackgroundColour(BGCOLOUR)
		p1.sizer = wx.BoxSizer(wx.VERTICAL)
		p1.SetSizer(p1.sizer)
		self.splitter.AppendWindow(p1)

		self.plot_mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
		p1.sizer.Add(self.plot_mode_sizer, flag=wx.ALIGN_CENTER | wx.TOP, border=12)
		
		# The order of the choice items is significant for compatibility
		# with LUTFrame:
		# 0 = vcgt,
		# 1 = [rgb]TRC
		# 2 = gamut
		self.plot_mode_select = wx.Choice(p1, -1, choices=[lang.getstr("vcgt"),
														   lang.getstr("[rgb]TRC"),
														   lang.getstr("gamut")])
		self.plot_mode_sizer.Add(self.plot_mode_select, flag=wx.ALIGN_CENTER_VERTICAL |
															 wx.LEFT, border=20)
		self.plot_mode_select.Bind(wx.EVT_CHOICE, self.plot_mode_select_handler)
		self.plot_mode_select.SetSelection(2)
		self.plot_mode_select.Disable()
		
		self.tooltip_btn = wx.StaticBitmap(p1, -1, geticon(16, "dialog-information"),
										   style=wx.NO_BORDER)
		self.tooltip_btn.SetBackgroundColour(BGCOLOUR)
		self.tooltip_btn.SetToolTipString(lang.getstr("gamut_plot.tooltip"))
		self.plot_mode_sizer.Add(self.tooltip_btn, flag=wx.ALIGN_CENTER_VERTICAL |
														wx.LEFT, border=8)

		self.save_plot_btn = wx.BitmapButton(p1, -1,
											 geticon(16, "media-floppy"),
											 style=wx.NO_BORDER)
		self.save_plot_btn.SetBackgroundColour(BGCOLOUR)
		self.save_plot_btn.Bind(wx.EVT_BUTTON, self.SaveFile)
		self.save_plot_btn.SetToolTipString(lang.getstr("save_as"))
		self.save_plot_btn.SetBitmapDisabled(geticon(16, "empty"))
		self.save_plot_btn.Disable()
		self.plot_mode_sizer.Add(self.save_plot_btn, flag=wx.ALIGN_CENTER_VERTICAL |
														  wx.LEFT, border=8)
		
		self.view_3d_btn = wx.BitmapButton(p1, -1, geticon(16, "3D"),
										   style=wx.NO_BORDER)
		self.view_3d_btn.SetBackgroundColour(BGCOLOUR)
		self.view_3d_btn.Bind(wx.EVT_BUTTON, self.view_3d)
		self.view_3d_btn.SetToolTipString(lang.getstr("view.3d"))
		self.view_3d_btn.SetBitmapDisabled(geticon(16, "empty"))
		self.view_3d_btn.Disable()
		self.plot_mode_sizer.Add(self.view_3d_btn, flag=wx.ALIGN_CENTER_VERTICAL |
														wx.LEFT, border=12)

		self.client = GamutCanvas(p1)
		p1.sizer.Add(self.client, 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT |
										  wx.TOP | wx.BOTTOM, border=4)
		
		self.options_panel = SimpleBook(p1)
		self.options_panel.SetBackgroundColour(BGCOLOUR)
		p1.sizer.Add(self.options_panel, flag=wx.EXPAND | wx.BOTTOM, border=12)
		
		# Gamut view options
		self.gamut_view_options = GamutViewOptions(p1)
		self.options_panel.AddPage(self.gamut_view_options, "")
		
		# Curve view options
		self.lut_view_options = wx.Panel(p1)
		self.lut_view_options.SetBackgroundColour(BGCOLOUR)
		self.lut_view_options_sizer = self.box_sizer = wx.FlexGridSizer(0, 3, 4, 4)
		self.lut_view_options_sizer.AddGrowableCol(0)
		self.lut_view_options_sizer.AddGrowableCol(2)
		self.lut_view_options.SetSizer(self.lut_view_options_sizer)
		self.options_panel.AddPage(self.lut_view_options, "")
		
		self.lut_view_options_sizer.Add((0, 0))
		
		hsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.lut_view_options_sizer.Add(hsizer, flag=wx.ALIGN_CENTER |
													 wx.BOTTOM, border=8)

		self.rendering_intent_select = wx.Choice(self.lut_view_options, -1,
												 choices=[lang.getstr("gamap.intents.a"),
														  lang.getstr("gamap.intents.r"),
														  lang.getstr("gamap.intents.p"),
														  lang.getstr("gamap.intents.s")])
		hsizer.Add(self.rendering_intent_select, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
				   border=10)
		self.rendering_intent_select.Bind(wx.EVT_CHOICE,
										  self.rendering_intent_select_handler)
		self.rendering_intent_select.SetSelection(1)
		
		self.direction_select = wx.Choice(self.lut_view_options, -1,
										  choices=[lang.getstr("direction.backward"),
												   lang.getstr("direction.forward.inverted")])
		hsizer.Add(self.direction_select, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
				   border=10)
		self.direction_select.Bind(wx.EVT_CHOICE, self.direction_select_handler)
		self.direction_select.SetSelection(0)
		
		self.lut_view_options_sizer.Add((0, 0))
		
		self.lut_view_options_sizer.Add((0, 0))
		
		hsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.lut_view_options_sizer.Add(hsizer, flag=wx.ALIGN_CENTER)
		
		hsizer.Add((16, 0))
		
		self.show_as_L = wx.CheckBox(self.lut_view_options, -1, u"L* \u2192")
		self.show_as_L.SetForegroundColour(FGCOLOUR)
		self.show_as_L.SetValue(True)
		hsizer.Add(self.show_as_L,
										flag=wx.ALIGN_CENTER_VERTICAL)
		self.Bind(wx.EVT_CHECKBOX, self.DrawLUT, id=self.show_as_L.GetId())
		
		self.toggle_red = wx.CheckBox(self.lut_view_options, -1, "R")
		self.toggle_red.SetForegroundColour(FGCOLOUR)
		self.toggle_red.SetValue(True)
		hsizer.Add(self.toggle_red,
										flag=wx.ALIGN_CENTER_VERTICAL)
		self.Bind(wx.EVT_CHECKBOX, self.DrawLUT, id=self.toggle_red.GetId())
		
		self.toggle_green = wx.CheckBox(self.lut_view_options, -1, "G")
		self.toggle_green.SetForegroundColour(FGCOLOUR)
		self.toggle_green.SetValue(True)
		hsizer.Add(self.toggle_green,
										flag=wx.ALIGN_CENTER_VERTICAL)
		self.Bind(wx.EVT_CHECKBOX, self.DrawLUT, id=self.toggle_green.GetId())
		
		self.toggle_blue = wx.CheckBox(self.lut_view_options, -1, "B")
		self.toggle_blue.SetForegroundColour(FGCOLOUR)
		self.toggle_blue.SetValue(True)
		hsizer.Add(self.toggle_blue,
										flag=wx.ALIGN_CENTER_VERTICAL)
		self.Bind(wx.EVT_CHECKBOX, self.DrawLUT, id=self.toggle_blue.GetId())
		
		self.toggle_clut = wx.CheckBox(self.lut_view_options, -1, "LUT")
		self.toggle_clut.SetForegroundColour(FGCOLOUR)
		hsizer.Add(self.toggle_clut, flag=wx.ALIGN_CENTER_VERTICAL |
												   wx.LEFT, border=16)
		self.Bind(wx.EVT_CHECKBOX, self.toggle_clut_handler,
				  id=self.toggle_clut.GetId())
		
		self.lut_view_options_sizer.Add((0, 0))
		
		p2 = wx.Panel(self.splitter)
		p2.SetBackgroundColour(gridbgcolor)
		p2.sizer = wx.BoxSizer(wx.VERTICAL)
		p2.SetSizer(p2.sizer)
		self.splitter.AppendWindow(p2)
		
		self.grid = ProfileInfoGrid(p2, -1)
		self.grid.CreateGrid(0, 2)
		self.grid.SetCellHighlightColour(gridbgcolor)
		self.grid.SetCellHighlightPenWidth(0)
		self.grid.SetCellHighlightROPenWidth(0)
		self.grid.SetDefaultCellBackgroundColour(gridbgcolor)
		self.grid.SetDefaultCellTextColour(TEXTCOLOUR)
		font = wx.Font(FONTSIZE_MEDIUM, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
					   wx.FONTWEIGHT_NORMAL)
		self.grid.SetDefaultCellFont(font)
		self.grid.SetDefaultRowSize(20)
		self.grid.SetLabelBackgroundColour(gridbgcolor)
		self.grid.SetRowLabelSize(20)
		self.grid.SetColLabelSize(0)
		self.grid.DisableDragRowSize()
		self.grid.EnableDragColSize()
		self.grid.EnableEditing(False)
		self.grid.EnableGridLines(False)
		self.grid.Bind(wx.grid.EVT_GRID_COL_SIZE, self.resize_grid)
		p2.sizer.Add(self.grid, 1, flag=wx.EXPAND, border=12)
		
		drophandlers = {
			".icc": self.drop_handler,
			".icm": self.drop_handler
		}
		droptarget = FileDrop(drophandlers, parent=self)
		self.title_panel.SetDropTarget(droptarget)
		droptarget = FileDrop(drophandlers, parent=self)
		self.title_txt.SetDropTarget(droptarget)
		droptarget = FileDrop(drophandlers, parent=self)
		self.client.SetDropTarget(droptarget)
		droptarget = FileDrop(drophandlers, parent=self)
		self.grid.SetDropTarget(droptarget)

		self.splitter.SetMinimumPaneSize(defaults["size.profile_info.w"] - self.splitter._GetSashSize())
		self.splitter.SetHSplit(0)
		
		border, titlebar = get_platform_window_decoration_size()
		self.SetSaneGeometry(
			getcfg("position.profile_info.x"),
			getcfg("position.profile_info.y"),
			getcfg("size.profile_info.w") + border * 2,
			getcfg("size.profile_info.h") + titlebar + border)
		self.SetMinSize((defaults["size.profile_info.w"] + border * 2,
						 defaults["size.profile_info.h"] + titlebar + border))
		self.splitter.SetSplitSize((getcfg("size.profile_info.split.w") + border * 2,
									self.GetSize()[1]))
		self.splitter.SetExpandedSize(self.GetSize())
		self.splitter.SetExpanded(0)
		
		self.client.canvas.Bind(wx.EVT_MOTION, self.OnMotion)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.Bind(wx.EVT_MOVE, self.OnMove)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnSashPosChanging)
		
		self.display_no = -1
		self.display_rects = get_display_rects()

		children = self.GetAllChildren()

		for child in children:
			if isinstance(child, wx.Choice):
				child.SetMaxFontSize(11)
			child.Bind(wx.EVT_KEY_DOWN, self.key_handler)
			child.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)

	def DrawCanvas(self, profile_no=None, reset=True):
		self.SetStatusText('')
		if self.plot_mode_select.GetSelection() == self.plot_mode_select.GetCount() - 1:
			# Gamut plot
			self.plot_mode_sizer.Show(self.tooltip_btn)
			self.plot_mode_sizer.Show(self.view_3d_btn)
			self.options_panel.GetCurrentPage().DrawCanvas(reset=reset)
			self.save_plot_btn.Enable()
			self.view_3d_btn.Enable()
		else:
			# Curves plot
			self.plot_mode_sizer.Hide(self.tooltip_btn)
			self.plot_mode_sizer.Hide(self.view_3d_btn)
			self.client.SetEnableCenterLines(True)
			self.client.SetEnableDiagonals('Bottomleft-Topright')
			self.client.SetEnableGrid(False)
			self.client.SetEnablePointLabel(True)
			if ("vcgt" in self.profile.tags or
				("rTRC" in self.profile.tags and
				 "gTRC" in self.profile.tags and
				 "bTRC" in self.profile.tags) or
				(("B2A0" in self.profile.tags or
				  "A2B0" in self.profile.tags) and
				 self.profile.colorSpace == "RGB")):
				self.toggle_red.Enable()
				self.toggle_green.Enable()
				self.toggle_blue.Enable()
				self.DrawLUT()
				self.handle_errors()
			else:
				self.toggle_red.Disable()
				self.toggle_green.Disable()
				self.toggle_blue.Disable()
				self.client.DrawLUT()
		self.splitter.GetTopLeft().sizer.Layout()
		self.splitter.GetTopLeft().Refresh()

	def LoadProfile(self, profile, reset=True):
		if not isinstance(profile, ICCP.ICCProfile):
			try:
				profile = ICCP.ICCProfile(profile)
			except (IOError, ICCP.ICCProfileInvalidError), exception:
				show_result_dialog(Error(lang.getstr("profile.invalid") + 
									     "\n" + profile), self)
				return
		self.profile = profile
		self.rTRC = profile.tags.get("rTRC")
		self.gTRC = profile.tags.get("gTRC")
		self.bTRC = profile.tags.get("bTRC")
		self.trc = None
		
		self.gamut_view_options.direction_select.Show("B2A0" in
													  self.profile.tags and
													  "A2B0" in
													  self.profile.tags)
		self.gamut_view_options.toggle_clut.SetValue("B2A0" in profile.tags or
													 "A2B0" in profile.tags)
		self.gamut_view_options.toggle_clut.Show("B2A0" in profile.tags or
												 "A2B0" in profile.tags)
		self.gamut_view_options.toggle_clut.Enable(isinstance(profile.tags.get("rTRC"),
															  ICCP.CurveType) and
												   isinstance(profile.tags.get("gTRC"),
															  ICCP.CurveType) and
												   isinstance(profile.tags.get("bTRC"),
															  ICCP.CurveType))
		self.toggle_clut.SetValue("B2A0" in profile.tags or
								  "A2B0" in profile.tags)
		
		plot_mode = self.plot_mode_select.GetSelection()
		plot_mode_count = self.plot_mode_select.GetCount()
		choice = []
		info = profile.get_info()
		self.client.errors = []
		if (("rTRC" in self.profile.tags and "gTRC" in self.profile.tags and
			 "bTRC" in self.profile.tags) or
			(("B2A0" in self.profile.tags or "A2B0" in self.profile.tags) and
			 self.profile.colorSpace == "RGB")):
			# vcgt needs to be in here for compatibility with LUTFrame
			choice.append(lang.getstr("vcgt"))
			try:
				self.lookup_tone_response_curves()
			except Exception, exception:
				show_result_dialog(exception, self)
			else:
				choice.append(lang.getstr("[rgb]TRC"))
		choice.append(lang.getstr("gamut"))
		self.Freeze()
		self.plot_mode_select.SetItems(choice)
		if plot_mode_count != self.plot_mode_select.GetCount():
			plot_mode = self.plot_mode_select.GetCount() - 1
		self.plot_mode_select.SetSelection(min(plot_mode,
											   self.plot_mode_select.GetCount() - 1))
		self.select_current_page()
		self.plot_mode_select.Enable()
		
		self.title_txt.SetLabel(profile.getDescription())
		border, titlebar = get_platform_window_decoration_size()
		titlewidth = self.title_txt.GetTextExtent(self.title_txt.GetLabel())[0] + 30
		if titlewidth > defaults["size.profile_info.w"]:
			defaults["size.profile_info.w"] = titlewidth
		if titlewidth > defaults["size.profile_info.split.w"]:
			defaults["size.profile_info.split.w"] = titlewidth
		if titlewidth + border * 2 > self.GetMinSize()[0]:
			self.SetMinSize((titlewidth + border * 2,
							 defaults["size.profile_info.h"] + titlebar + border))
			if titlewidth + border * 2 > self.GetSize()[0]:
				self.SetSize((self.get_platform_window_size()[0],
							  self.GetSize()[1]))
				self.splitter.SetExpandedSize(self.get_platform_window_size())
		
		rows = [("", "")]
		lines = []
		for label, value in info:
			label = label.replace("\0", "")
			value = wrap(universal_newlines(value.strip()).replace("\t", "\n"),
						 52).replace("\0", "").split("\n")
			linecount = len(value)
			for i, line in enumerate(value):
				value[i] = line.strip()
			label = universal_newlines(label).split("\n")
			while len(label) < linecount:
				label.append("")
			lines.extend(zip(label, value))
		for i, line in enumerate(lines):
			line = list(line)
			indent = re.match("\s+", line[0])
			if indent:
				#if i + 1 < len(lines) and lines[i + 1][0].startswith(" "):
					#marker = u" ├  "
				#else:
					#marker = u" └  "
				line[0] = indent.group() + lang.getstr(line[0].strip())
			elif line[0]:
				#if i + 1 < len(lines) and lines[i + 1][0].startswith(" "):
					#marker = u"▼ "
				#else:
					#marker = u"► "
				line[0] = lang.getstr(line[0])
			line[1] = lang.getstr(line[1])
			rows.append(line)
		
		rows.append(("", ""))
		
		if self.grid.GetNumberRows():
			self.grid.DeleteRows(0, self.grid.GetNumberRows())
		self.grid.AppendRows(len(rows))
		labelcolor = wx.Colour(0x80, 0x80, 0x80)
		altcolor = wx.Colour(230, 230, 230)
		namedcolor = False
		for i, (label, value) in enumerate(rows):
			self.grid.SetCellValue(i, 0, " " + label)
			if i % 2:
				self.grid.SetCellBackgroundColour(i, 0, altcolor)
				self.grid.SetCellBackgroundColour(i, 1, altcolor)
			if label == lang.getstr(ICCP.tags["ncl2"]):
				namedcolor = True
			elif label.strip() and label.lstrip() == label:
				namedcolor = False
			if namedcolor:
				color = re.match("(Lab|XYZ)((?:\s+-?\d+(?:\.\d+)){3,})", value)
			else:
				color = None
			if color:
				if color.groups()[0] == "Lab":
					color = colormath.Lab2RGB(*[float(v) for v in
												color.groups()[1].strip().split()],
											  **dict(scale=255))
				else:
					# XYZ
					color = colormath.XYZ2RGB(*[float(v) for v in
												color.groups()[1].strip().split()],
											  **dict(scale=255))
				labelbgcolor = wx.Colour(*[int(round(v)) for v in color])
			else:
				labelbgcolor = self.grid.GetCellBackgroundColour(i, 0)
			self.grid.SetRowLabelRenderer(i, ProfileInfoRowLabelRenderer(labelbgcolor))
			self.grid.SetCellTextColour(i, 0, labelcolor)
			self.grid.SetCellValue(i, 1, value)
		
		self.grid.AutoSizeColumn(0)
		self.resize_grid()
		self.Layout()
		self.DrawCanvas(reset=reset)
		self.Thaw()
	
	def OnClose(self, event):
		self.worker.wrapup(False)
		event.Skip()

	def OnMotion(self, event):
		if isinstance(event, wx.MouseEvent):
			xy = self.client._getXY(event)
		else:
			xy = event
		if self.plot_mode_select.GetSelection() < self.plot_mode_select.GetCount() - 1:
			# Curves plot
			if isinstance(event, wx.MouseEvent):
				if not event.LeftIsDown():
					self.UpdatePointLabel(xy)
				else:
					self.client.erase_pointlabel()
		else:
			# Gamut plot
			if self.options_panel.GetCurrentPage().colorspace_select.GetSelection() == 0:
				format = "%.2f %.2f"
			else:
				format = "%.4f %.4f"
			page = self.options_panel.GetCurrentPage()
			colorspace_no = page.colorspace_select.GetSelection()
			whitepoint_no = page.whitepoint_select.GetSelection()
			if whitepoint_no > 0:
				if colorspace_no == 0:
					# a*b*
					x, y, Y = colormath.Lab2xyY(100.0, xy[0], xy[1])
				elif colorspace_no == 1:
					# u' v'
					x, y = colormath.u_v_2xy(xy[0], xy[1])
				elif colorspace_no in (3, 4, 5, 6):
					# DIN99
					L99 = colormath.Lab2DIN99(100, 0, 0)[0]
					if colorspace_no == 4:
						# DIN99b
						a, b = colormath.DIN99b2Lab(L99, xy[0], xy[1])[1:]
					elif colorspace_no == 5:
						# DIN99c
						a, b = colormath.DIN99c2Lab(L99, xy[0], xy[1])[1:]
					elif colorspace_no == 6:
						# DIN99d
						a, b = colormath.DIN99d2Lab(L99, xy[0], xy[1])[1:]
					else:
						a, b = colormath.DIN992Lab(L99, xy[0], xy[1])[1:]
					x, y = colormath.Lab2xyY(100.0, a, b)[:2]
				else:
					# xy
					x, y = xy
				cct, delta = colormath.xy_CCT_delta(x, y,
													daylight=whitepoint_no == 1)
				status = format % xy
				if cct:
					if delta:
						locus = {"Blackbody": "blackbody",
								 "Daylight": "daylight"}.get(page.whitepoint_select.GetStringSelection(),
															 page.whitepoint_select.GetStringSelection())
						status = u"%s, CCT %i (%s %.2f)" % (
							format % xy, cct, lang.getstr("delta_e_to_locus", 
														  locus),
							delta["E"])
					else:
						status = u"%s, CCT %i" % (format % xy, cct)
				self.SetStatusText(status)
			else:
				self.SetStatusText(format % xy)
		if isinstance(event, wx.MouseEvent):
			event.Skip() # Go to next handler

	def OnMove(self, event=None):
		if self.IsShownOnScreen() and not \
		   self.IsMaximized() and not self.IsIconized():
			x, y = self.GetScreenPosition()
			setcfg("position.profile_info.x", x)
			setcfg("position.profile_info.y", y)
		if event:
			event.Skip()
	
	def OnSashPosChanging(self, event):
		border, titlebar = get_platform_window_decoration_size()
		self.splitter.SetExpandedSize((self.splitter._splitx +
									   self.splitter._GetSashSize() +
									   border * 2,
									   self.GetSize()[1]))
		setcfg("size.profile_info.w", self.splitter._splitx +
									  self.splitter._GetSashSize())
		wx.CallAfter(self.redraw)
		wx.CallAfter(self.resize_grid)
	
	def OnSize(self, event=None):
		if self.IsShownOnScreen() and self.IsMaximized():
			self.splitter.AdjustLayout()
		self.splitter.Refresh()
		wx.CallAfter(self.redraw)
		wx.CallAfter(self.resize_grid)
		if self.IsShownOnScreen() and not self.IsIconized():
			wx.CallAfter(self._setsize)
		if event:
			event.Skip()
	
	def OnWheel(self, event):
		xy = wx.GetMousePosition()
		if not self.client.GetClientRect().Contains(self.client.ScreenToClient(xy)):
			if self.grid.GetClientRect().Contains(self.grid.ScreenToClient(xy)):
				self.grid.SetFocus()
			event.Skip()
		elif self.client.last_draw:
			if event.WheelRotation < 0:
				direction = 1.0
			else:
				direction = -1.0
			self.client.zoom(direction)
	
	def _setsize(self):
		if not self.IsMaximized():
			w, h = self.GetSize()
			border, titlebar = get_platform_window_decoration_size()
			if self.splitter._expanded < 0:
				self.splitter.SetExpandedSize((self.splitter._splitx +
											   self.splitter._GetSashSize() +
											   border * 2,
											   self.GetSize()[1]))
				self.splitter.SetSplitSize((w, self.GetSize()[1]))
				setcfg("size.profile_info.w", self.splitter._splitx +
											  self.splitter._GetSashSize())
				setcfg("size.profile_info.split.w", w - border * 2)
			else:
				self.splitter.SetExpandedSize((w, self.GetSize()[1]))
				setcfg("size.profile_info.w", w - border * 2)
			setcfg("size.profile_info.h", h - titlebar - border)
	
	def drop_handler(self, path):
		"""
		Drag'n'drop handler for .cal/.icc/.icm files.
		
		"""
		self.LoadProfile(path, reset=False)


	def get_platform_window_size(self, defaultwidth=None, defaultheight=None,
								 split=False):
		if split:
			name = ".split"
		else:
			name = ""
		if not defaultwidth:
			defaultwidth = defaults["size.profile_info%s.w" % name]
		if not defaultheight:
			defaultheight = defaults["size.profile_info.h"]
		border, titlebar = get_platform_window_decoration_size()
		#return (max(max(getcfg("size.profile_info%s.w" % name),
						#defaultwidth) + border * 2, self.GetMinSize()[0]),
				#max(getcfg("size.profile_info.h"),
					#defaultheight) + titlebar + border)
		if split:
			w, h = self.splitter.GetSplitSize()
		else:
			w, h = self.splitter.GetExpandedSize()
		return (max(w, defaultwidth + border * 2, self.GetMinSize()[0]),
				max(h, defaultheight + titlebar + border))

	def key_handler(self, event):
		# AltDown
		# CmdDown
		# ControlDown
		# GetKeyCode
		# GetModifiers
		# GetPosition
		# GetRawKeyCode
		# GetRawKeyFlags
		# GetUniChar
		# GetUnicodeKey
		# GetX
		# GetY
		# HasModifiers
		# KeyCode
		# MetaDown
		# Modifiers
		# Position
		# RawKeyCode
		# RawKeyFlags
		# ShiftDown
		# UnicodeKey
		# X
		# Y
		key = event.GetKeyCode()
		if (event.ControlDown() or event.CmdDown()): # CTRL (Linux/Mac/Windows) / CMD (Mac)
			focus = self.FindFocus()
			if focus and self.grid in (focus, focus.GetParent(),
									   focus.GetGrandParent()):
				if key == 65: # A
					self.grid.SelectAll()
					return
				elif key in (67, 88): # C / X
					clip = []
					cells = self.grid.GetSelection()
					i = -1
					start_col = self.grid.GetNumberCols()
					for cell in cells:
						row = cell[0]
						col = cell[1]
						if i < row:
							clip += [[]]
							i = row
						if col < start_col:
							start_col = col
						while len(clip[-1]) - 1 < col:
							clip[-1] += [""]
						clip[-1][col] = self.grid.GetCellValue(row, col)
					for i, row in enumerate(clip):
						clip[i] = "\t".join(row[start_col:])
					clipdata = wx.TextDataObject()
					clipdata.SetText("\n".join(clip))
					wx.TheClipboard.Open()
					wx.TheClipboard.SetData(clipdata)
					wx.TheClipboard.Close()
					return
			if key == 83 and self.profile: # S
				self.SaveFile()
				return
			else:
				event.Skip()
		elif key in (43, wx.WXK_NUMPAD_ADD):
			# + key zoom in
			self.client.zoom(-1)
		elif key in (45, wx.WXK_NUMPAD_SUBTRACT):
			# - key zoom out
			self.client.zoom(1)
		else:
			event.Skip()
	
	def plot_mode_select_handler(self, event):
		self.Freeze()
		self.select_current_page()
		reset = (self.plot_mode_select.GetSelection() ==
				 self.plot_mode_select.GetCount() - 1)
		if not reset:
			self.client.resetzoom()
		self.DrawCanvas(reset=reset)
		if not reset:
			wx.CallAfter(self.client.center)
		self.Thaw()
	
	def redraw(self):
		if self.plot_mode_select.GetSelection() == self.plot_mode_select.GetCount() - 1 and self.client.last_draw:
			# Update gamut plot
			self.client.Parent.Freeze()
			self.client._DrawCanvas(self.client.last_draw[0])
			self.client.Parent.Thaw()
	
	def resize_grid(self, event=None):
		self.grid.SetColSize(1, max(self.grid.GetSize()[0] -
									self.grid.GetRowLabelSize() -
									self.grid.GetColSize(0) -
									wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X),
									0))
		self.grid.SetMargins(0 - wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X),
							 0 - wx.SystemSettings_GetMetric(wx.SYS_HSCROLL_Y))
		self.grid.ForceRefresh()
	
	def select_current_page(self):
		if self.plot_mode_select.GetSelection() == self.plot_mode_select.GetCount() - 1:
			# Gamut plot
			self.options_panel.SetSelection(0)
		else:
			# Curves plot
			self.options_panel.SetSelection(1)
		self.splitter.GetTopLeft().Layout()
	
	def view_3d(self, event):
		profile = self.profile
		if not profile:
			vrmlfile2x3dhtmlfile(view=True)
		else:
			if profile.fileName and os.path.isfile(profile.fileName):
				profile_path = profile.fileName
			else:
				result = self.worker.create_tempdir()
				if isinstance(result, Exception):
					show_result_dialog(result, self)
					return
				desc = profile.getDescription()
				profile_path = os.path.join(self.worker.tempdir,
											make_argyll_compatible_path(desc) +
											profile_ext)
				profile.write(profile_path)
			filename, ext = os.path.splitext(profile_path)
			htmlpath = filename + ".x3d.html"
			if os.path.isfile(htmlpath):
				# The X3D HTML file seems to already exist
				launch_file(htmlpath)
			else:
				for vrmlext in (".vrml", ".vrml.gz", ".wrl", ".wrl.gz", ".wrz"):
					vrmlpath = filename + vrmlext
					if os.path.isfile(vrmlpath):
						break
				if os.path.isfile(vrmlpath):
					self.view_3d_consumer(True, None, vrmlpath, htmlpath)
				else:
					# Create VRML file
					self.worker.start(self.view_3d_consumer,
									  self.worker.calculate_gamut,
									  cargs=(filename, None, htmlpath),
									  wargs=(profile_path, False),
									  progress_msg=lang.getstr("gamut.view.create"))
	
	def view_3d_consumer(self, result, filename, vrmlpath, htmlpath):
		if isinstance(result, Exception):
			show_result_dialog(result, self)
		else:
			if filename:
				if getcfg("vrml.compress"):
					vrmlpath = filename + ".wrz"
				else:
					vrmlpath = filename + ".wrl"
			vrmlfile2x3dhtmlfile(vrmlpath, htmlpath, view=True)

class ProfileInfoGrid(wx.grid.Grid):

	def __init__(self, *args, **kwargs):
		wx.grid.Grid.__init__(self, *args, **kwargs)
		self.GetGridRowLabelWindow().Bind(wx.EVT_PAINT, self._onPaintRowLabels)
		
		self._rowRenderers = {}

	def _getRowTopBottom(self, row):
		r = 0
		top = 0
		while r < row:
			top += self.GetRowSize(r)
			r += 1
		bottom = top + self.GetRowSize(row) - 1
		return top, bottom

	def _onPaintRowLabels(self, evt):
		window = evt.GetEventObject()
		dc = wx.PaintDC(window)

		if getattr(self, "CalcRowLabelsExposed", None):
			# wxPython >= 2.8.10
			rows = self.CalcRowLabelsExposed(window.GetUpdateRegion())
			if rows == [-1]:
				return
		else:
			# wxPython < 2.8.10
			rows = xrange(self.GetNumberRows())
			if not rows:
				return

		x, y = self.CalcUnscrolledPosition((0,0))
		pt = dc.GetDeviceOrigin()
		dc.SetDeviceOrigin(pt.x, pt.y-y)
		for row in rows:
			top, bottom = self._getRowTopBottom(row)
			rect = wx.Rect()
			rect.top = top
			rect.bottom = bottom
			rect.x = 0
			rect.width = self.GetRowLabelSize()

			renderer = self._rowRenderers.get(row, None) or \
					   ProfileInfoRowLabelRenderer(self.GetLabelBackgroundColour(row, 0))
			renderer.Draw(self, dc, rect, row)
        
	def SetRowLabelRenderer(self, row, renderer):
		"""
		Register a renderer to be used for drawing the label for the
		given row.
		"""
		if renderer is None:
			if row in self._rowRenderers:
				del self._rowRenderers[row]
		else:
			self._rowRenderers[row] = renderer


class ProfileInfoRowLabelRenderer(object):

	def __init__(self, bgcolor):
		self._bgcolor = bgcolor

	def Draw(self, grid, dc, rect, row):
		dc.SetBrush(wx.Brush(self._bgcolor))
		dc.SetPen(wx.TRANSPARENT_PEN)
		dc.DrawRectangleRect(rect)


class ProfileInfoViewer(wx.App):

	def OnInit(self):
		check_set_argyll_bin()
		self.frame = ProfileInfoFrame(None, -1)
		return True


def main(profile=None):
	config.initcfg()
	lang.init()
	lang.update_defaults()
	app = ProfileInfoViewer(0)
	display_no = get_argyll_display_number(app.frame.get_display()[1])
	app.frame.LoadProfile(profile or get_display_profile(display_no))
	app.frame.Show()
	app.MainLoop()
	writecfg()

if __name__ == "__main__":
	main(*sys.argv[max(len(sys.argv) - 1, 1):])
