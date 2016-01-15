#!/usr/bin/env python2
# -*- coding: utf-8 -*-

""" 
Set ICC profiles and load calibration curves for all configured display devices

"""

import os
import sys
import threading
import time

from meta import name as appname, version


class ProfileLoader(object):

	def __init__(self):
		import config
		from config import appbasename
		from worker import Worker
		from wxwindows import wx
		if not wx.GetApp():
			app = wx.App(0)
		else:
			app = None
		self.worker = Worker()
		self.reload_count = 0
		self.lock = threading.Lock()
		self.monitors = []
		self.devices2profiles = {}
		self._skip = "--skip" in sys.argv[1:]
		self._force_reload = False
		self._madvr_instances = []
		self._timestamp = time.time()
		apply_profiles = ("--force" in sys.argv[1:] or
						  config.getcfg("profile.load_on_login"))
		##if (sys.platform == "win32" and not "--force" in sys.argv[1:] and
			##sys.getwindowsversion() >= (6, 1)):
			##from util_win import calibration_management_isenabled
			##if calibration_management_isenabled():
				### Incase calibration loading is handled by Windows 7 and
				### isn't forced
				##apply_profiles = False
		if (sys.platform != "win32" and
			apply_profiles and not self._skip and
			not os.path.isfile(os.path.join(config.confighome,
											appbasename + ".lock")) and
			not self._is_madvr_running(True)):
			self.apply_profiles_and_warn_on_error()
		if sys.platform == "win32":
			# We create a TSR tray program only under Windows.
			# Linux has colord/Oyranos and respective session daemons should
			# take care of calibration loading
			import ctypes
			import localization as lang
			import madvr
			from log import safe_print
			from util_str import safe_unicode
			from util_win import calibration_management_isenabled
			from wxwindows import BaseFrame

			class PLFrame(BaseFrame):

				def __init__(self, pl):
					BaseFrame.__init__(self, None)
					self.pl = pl
					self.Bind(wx.EVT_CLOSE, pl.exit)

				def get_commands(self):
					return self.get_common_commands() + ["apply-profiles"]

				def process_data(self, data):
					if data[0] == "apply-profiles" and len(data) == 1:
						if (not "--force" in sys.argv[1:] and
							calibration_management_isenabled()):
							return lang.getstr("calibration.load.handled_by_os")
						if (os.path.isfile(os.path.join(config.confighome,
													    appbasename + ".lock")) or
							self.pl._is_madvr_running()):
							return "forbidden"
						elif sys.platform == "win32":
							self.pl._set_force_reload()
						else:
							self.pl.apply_profiles(True)
						return self.pl.errors or "ok"
					return "invalid"

			self.frame = PLFrame(self)

			class TaskBarIcon(wx.TaskBarIcon):

				def __init__(self, pl):
					super(TaskBarIcon, self).__init__()
					self.pl = pl
					self.balloon_text = None
					bitmap = config.geticon(16, appname + "-apply-profiles")
					icon = wx.EmptyIcon()
					icon.CopyFromBitmap(bitmap)
					self._active_icon = icon
					# Use Rec. 709 luma coefficients to convert to grayscale
					image = bitmap.ConvertToImage().ConvertToGreyscale(.2126,
																	   .7152,
																	   .0722)
					icon = wx.EmptyIcon()
					icon.CopyFromBitmap(image.ConvertToBitmap())
					self._inactive_icon = icon
					self.set_visual_state(True)
					self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

				def CreatePopupMenu(self):
					# Popup menu appears on right-click
					menu = wx.Menu()
					
					if (os.path.isfile(os.path.join(config.confighome,
												   appbasename + ".lock")) or
						self.pl._is_madvr_running()):
						reload_auto = reload_manual = None
					else:
						##method = self.pl.apply_profiles_and_warn_on_error
						reload_manual = self.pl._set_force_reload
						reload_auto = self.set_auto_reload
					for (label, method, checkable,
						 option) in (("calibration.reload_from_display_profiles",
									  reload_manual, False, None),
									 ("calibration.reload_automatically",
									  reload_auto, True,
									  "profile.load_on_login"),
									 ("profile_loader.fix_profile_associations",
									  self.pl._toggle_fix_profile_associations,
									  True,
									  "profile_loader.fix_profile_associations"),
									 ("-", None, False, None),
									 ("menuitem.quit", self.pl.exit, False,
									  None)):
						if label == "-":
							menu.AppendSeparator()
						else:
							if checkable:
								kind = wx.ITEM_CHECK
							else:
								kind = wx.ITEM_NORMAL
							item = wx.MenuItem(menu, -1, lang.getstr(label),
											   kind=kind)
							if method is None:
								item.Enable(False)
							else:
								menu.Bind(wx.EVT_MENU, method, id=item.Id)
							menu.AppendItem(item)
							if checkable:
								item.Check(bool(config.getcfg(option)))

					return menu

				def on_left_down(self, event):
					self.show_balloon()

				def set_auto_reload(self, event):
					config.setcfg("profile.load_on_login",
								  int(event.IsChecked()))
					self.set_visual_state()

				def set_visual_state(self, first_run=False):
					if self.pl._should_apply_profiles(first_run):
						icon = self._active_icon
					else:
						icon = self._inactive_icon
					self.SetIcon(icon, self.pl.get_title())

				def show_balloon(self, text=None, sticky=False):
					if wx.VERSION < (3, ):
						return
					if sticky:
						self.balloon_text = text
					elif text:
						self.balloon_text = None
					else:
						text = self.balloon_text
					if not text:
						if (not "--force" in sys.argv[1:] and
							calibration_management_isenabled()):
							text = lang.getstr("calibration.load.handled_by_os") + "\n"
						else:
							text = ""
						text += lang.getstr("calibration.reload.info",
											self.pl.reload_count)
					self.ShowBalloon(self.pl.get_title(), text, 100)

			self.taskbar_icon = TaskBarIcon(self)

			try:
				self.gdi32 = ctypes.windll.gdi32
				self.gdi32.GetDeviceGammaRamp.restype = ctypes.c_bool
				self.gdi32.SetDeviceGammaRamp.restype = ctypes.c_bool
			except Exception, exception:
				self.gdi32 = None
				safe_print(exception)
				self.taskbar_icon.show_balloon(safe_unicode(exception))

			try:
				self.madvr = madvr.MadTPG()
			except Exception, exception:
				safe_print(exception)
				if safe_unicode(exception) != lang.getstr("madvr.not_found"):
					self.taskbar_icon.show_balloon(safe_unicode(exception))
			else:
				self.madvr.add_connection_callback(self._madvr_connection_callback,
												   None, "madVR")
				self.madvr.add_connection_callback(self._madvr_connection_callback,
												   None, "madTPG")
				self.madvr.listen()
				self.madvr.announce()

			self.frame.listen()

			self._check_display_conf_thread = threading.Thread(target=self._check_display_conf)
			self._check_display_conf_thread.start()

			if app:
				app.MainLoop()

	def apply_profiles(self, event=None, index=None):
		import config
		import localization as lang
		from log import safe_print
		from util_os import which
		from worker import Worker, get_argyll_util

		if sys.platform == "win32":
			self.lock.acquire()

		worker = self.worker

		errors = self.errors = []

		if sys.platform == "win32":
			separator = "-"
		else:
			separator = "="
		safe_print(separator * 80)
		safe_print(lang.getstr("calibration.loading_from_display_profile"))

		# dispwin sets the _ICC_PROFILE(_n) root window atom, per-output xrandr 
		# _ICC_PROFILE property (if xrandr is working) and loads the vcgt for the 
		# requested screen (ucmm backend using color.jcnf), and has to be called 
		# multiple times to setup multiple screens.
		#
		# If there is no profile configured in ucmm for the requested screen (or 
		# ucmm support has been removed, like in the Argyll CMS versions shipped by 
		# recent Fedora releases), it falls back to a possibly existing per-output 
		# xrandr _ICC_PROFILE property (if xrandr is working) or _ICC_PROFILE(_n) 
		# root window atom.
		dispwin = get_argyll_util("dispwin")
		if index is None:
			if dispwin:
				worker.enumerate_displays_and_ports(silent=True, check_lut_access=False,
													enumerate_ports=False,
													include_network_devices=False)
				self.monitors = []
				if sys.platform == "win32" and worker.displays:
					self._enumerate_monitors()
			else:
				errors.append(lang.getstr("argyll.util.not_found", "dispwin"))

		if sys.platform != "win32":
			# gcm-apply sets the _ICC_PROFILE root window atom for the first screen, 
			# per-output xrandr _ICC_PROFILE properties (if xrandr is working) and 
			# loads the vcgt for all configured screens (device-profiles.conf)
			# NOTE: gcm-apply is no longer part of GNOME Color Manager since the 
			# introduction of colord as it's no longer needed
			gcm_apply = which("gcm-apply")
			if gcm_apply:
				worker.exec_cmd(gcm_apply, capture_output=True, skip_scripts=True,
								silent=False)

			# oyranos-monitor sets _ICC_PROFILE(_n) root window atoms (oyranos 
			# db backend) and loads the vcgt for all configured screens when 
			# xcalib is installed
			oyranos_monitor = which("oyranos-monitor")
			xcalib = which("xcalib")

		self.profile_associations = {}
		results = []
		for i, display in enumerate([display.replace("[PRIMARY]", 
													 lang.getstr("display.primary")) 
									 for display in worker.displays]):
			if config.is_virtual_display(i) or (index is not None
												and i != index):
				continue
			# Load profile and set vcgt
			if sys.platform != "win32" and oyranos_monitor:
				display_conf_oy_compat = worker.check_display_conf_oy_compat(i + 1)
				if display_conf_oy_compat:
					worker.exec_cmd(oyranos_monitor, 
									["-x", str(worker.display_rects[i][0]), 
									 "-y", str(worker.display_rects[i][1])], 
									capture_output=True, skip_scripts=True, 
									silent=False)
			if dispwin:
				profile_arg = worker.get_dispwin_display_profile_argument(i)
				if os.path.isabs(profile_arg) and os.path.isfile(profile_arg):
					mtime = os.stat(profile_arg).st_mtime
				else:
					mtime = 0
				self.profile_associations[i] = (os.path.basename(profile_arg),
												mtime)
				if (sys.platform == "win32" or not oyranos_monitor or
					not display_conf_oy_compat or not xcalib or profile_arg == "-L"):
					# Only need to run dispwin if under Windows, or if nothing else
					# has already taken care of display profile and vcgt loading
					# (e.g. oyranos-monitor with xcalib, or colord)
					if worker.exec_cmd(dispwin, ["-v", "-d%i" % (i + 1), "-c", 
												 profile_arg], 
									   capture_output=True, skip_scripts=True, 
									   silent=False):
						errortxt = ""
					else:
						errortxt = "\n".join(worker.errors).strip()
					if errortxt and ((not "using linear" in errortxt and
									  not "assuming linear" in errortxt) or 
									 len(errortxt.split("\n")) > 1):
						if "Failed to get the displays current ICC profile" in errortxt:
							# Maybe just not configured
							continue
						elif sys.platform == "win32" or \
						   "Failed to set VideoLUT" in errortxt or \
						   "We don't have access to the VideoLUT" in errortxt:
							errstr = lang.getstr("calibration.load_error")
						else:
							errstr = lang.getstr("profile.load_error")
						errors.append(": ".join([display, errstr]))
						continue
					else:
						results.append(display)
				if (config.getcfg("profile_loader.verify_calibration")
					or "--verify" in sys.argv[1:]):
					# Verify the calibration was actually loaded
					worker.exec_cmd(dispwin, ["-v", "-d%i" % (i + 1), "-V",
											  profile_arg], 
									capture_output=True, skip_scripts=True, 
									silent=False)
					# The 'NOT loaded' message goes to stdout!
					# Other errors go to stderr
					errortxt = "\n".join(worker.errors + worker.output).strip()
					if "NOT loaded" in errortxt or \
					   "We don't have access to the VideoLUT" in errortxt:
						errors.append(": ".join([display, 
												lang.getstr("calibration.load_error")]))

		if sys.platform == "win32":
			self.lock.release()
			if event:
				self.notify(results, errors)

		return errors

	def notify(self, results, errors, sticky=False):
		from wxwindows import wx
		if results:
			import localization as lang
			self.reload_count += 1
			results.insert(0, lang.getstr("calibration.load_success"))
		results.extend(errors)
		wx.CallAfter(lambda: self and self.taskbar_icon.set_visual_state())
		wx.CallAfter(lambda text, sticky: self and
										  self.taskbar_icon.show_balloon(text,
																		 sticky),
					 "\n".join(results), sticky)

	def apply_profiles_and_warn_on_error(self, event=None, index=None):
		errors = self.apply_profiles(event, index)
		import config
		if (errors and (config.getcfg("profile_loader.error.show_msg") or
						"--error-dialog" in sys.argv[1:]) and
			not "--silent" in sys.argv[1:]):
			import localization as lang
			from wxwindows import InfoDialog, wx
			dlg = InfoDialog(None, msg="\n".join(errors), 
							 title=self.get_title(),
							 ok=lang.getstr("ok"),
							 bitmap=config.geticon(32, "dialog-error"),
							 show=False)
			dlg.SetIcons(config.get_icon_bundle([256, 48, 32, 16],
						 appname + "-apply-profiles"))
			dlg.do_not_show_again_cb = wx.CheckBox(dlg, -1, lang.getstr("dialog.do_not_show_again"))
			dlg.do_not_show_again_cb.SetValue(not bool(config.getcfg("profile_loader.error.show_msg")))
			def do_not_show_again_handler(event=None):
				config.setcfg("profile_loader.error.show_msg",
							  int(not dlg.do_not_show_again_cb.GetValue()))
				config.writecfg()
			dlg.do_not_show_again_cb.Bind(wx.EVT_CHECKBOX, do_not_show_again_handler)
			dlg.sizer3.Add(dlg.do_not_show_again_cb, flag=wx.TOP, border=12)
			dlg.sizer0.SetSizeHints(dlg)
			dlg.sizer0.Layout()
			dlg.Center(wx.BOTH)
			dlg.ok.SetDefault()
			dlg.ShowModalThenDestroy()

	def exit(self, event=None):
		from util_win import calibration_management_isenabled
		from wxwindows import ConfirmDialog, wx
		if (self.frame and event.GetEventType() == wx.EVT_MENU.typeId and
			not calibration_management_isenabled()):
			import config
			import localization as lang
			from wxwindows import ConfirmDialog, wx
			dlg = ConfirmDialog(None, msg=lang.getstr("profile_loader.exit_warning"), 
								title=self.get_title(),
								ok=lang.getstr("menuitem.quit"), 
								bitmap=config.geticon(32, "dialog-warning"))
			dlg.SetIcons(config.get_icon_bundle([256, 48, 32, 16],
						 appname + "-apply-profiles"))
			result = dlg.ShowModal()
			dlg.Destroy()
			if result != wx.ID_OK:
				return
		self.frame and self.frame.Destroy()
		self.taskbar_icon and self.taskbar_icon.Destroy()

	def get_title(self):
		import localization as lang
		title = "%s %s %s" % (appname, lang.getstr("profile_loader").title(),
							  version)
		if "--force" in sys.argv[1:]:
			title += " (%s)" % lang.getstr("forced")
		return title

	def _check_display_conf(self):
		import ctypes
		import struct
		import _winreg

		import win32gui

		import config
		from config import appbasename, getcfg
		from defaultpaths import iccprofiles
		import ICCProfile as ICCP
		from wxwindows import wx
		import localization as lang
		from log import safe_print
		from util_win import get_active_display_device

		display = None
		current_display = None
		current_timestamp = 0
		first_run = True
		self.profile_associations = {}
		self.profiles = {}
		displaycal_lockfile = os.path.join(config.confighome, appbasename + ".lock")
		displaycal_running = os.path.isfile(displaycal_lockfile)
		while wx.GetApp():
			results = []
			errors = []
			apply_profiles = self._should_apply_profiles(first_run)
			##if not apply_profiles:
				##self.profile_associations = {}
			# Check if display configuration changed
			try:
				key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 
									  r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Configuration")
			except WindowsError:
				key = None
				numsubkeys = 0
				if not self.monitors:
					self._enumerate_monitors()
			else:
				numsubkeys, numvalues, mtime = _winreg.QueryInfoKey(key)
			for i in xrange(numsubkeys):
				subkey = _winreg.OpenKey(key, _winreg.EnumKey(key, i))
				display = _winreg.QueryValueEx(subkey, "SetId")[0]
				timestamp = struct.unpack("<Q", _winreg.QueryValueEx(subkey, "Timestamp")[0].rjust(8, '0'))
				if timestamp > current_timestamp:
					if display != current_display:
						if not first_run and apply_profiles:
							safe_print(lang.getstr("display_detected"))
							# One second delay to allow display configuration
							# to settle
							time.sleep(1)
							##self.apply_profiles(True)
							##apply_profiles = False
						if not first_run or not self.monitors:
							##self.worker.enumerate_displays_and_ports(silent=True, check_lut_access=False,
																	 ##enumerate_ports=False,
																	 ##include_network_devices=False)
							self._enumerate_monitors()
							if getcfg("profile_loader.fix_profile_associations"):
								# Work-around long-standing bug in applications
								# querying the monitor profile not making sure
								# to use the active display (this affects Windows
								# itself as well) when only one display is
								# active in a multi-monitor setup.
								if not first_run:
									self._reset_display_profile_associations()
								self._set_display_profiles()
					current_display = display
					current_timestamp = timestamp
				_winreg.CloseKey(subkey)
			if key:
				_winreg.CloseKey(key)
			# Check profile associations
			if apply_profiles or first_run:
				##self.lock.acquire()
				for i, (display, moninfo) in enumerate(self.monitors):
					try:
						profile = ICCP.get_display_profile(i, path_only=True)
					except IndexError:
						break
					except:
						continue
					profile_path = os.path.join(iccprofiles[0], profile)
					if os.path.isfile(profile_path):
						mtime = os.stat(profile_path).st_mtime
					else:
						mtime = 0
					if self.profile_associations.get(i) != (profile, mtime):
						if not first_run:
							device = get_active_display_device(moninfo["Device"])
							if not device:
								continue
							safe_print(lang.getstr("display_detected"))
							safe_print(display, "->", profile)
							##self.lock.release()
							##self.apply_profiles(True, index=i)
							##self.lock.acquire()
							##apply_profiles = False
							self.devices2profiles[device.DeviceKey] = (device.DeviceString,
																	   profile)
						self.profile_associations[i] = (profile, mtime)
						self.profiles[profile] = None
					# Check video card gamma table and (re)load calibration if
					# necessary
					if not apply_profiles or not self.gdi32:
						continue
					# Get display profile
					if not self.profiles.get(profile):
						try:
							self.profiles[profile] = ICCP.ICCProfile(profile)
							self.profiles[profile].tags.get("vcgt")
						except Exception, exception:
							continue
					profile = self.profiles[profile]
					vcgt_values = ([], [], [])
					if isinstance(profile.tags.get("vcgt"),
								  ICCP.VideoCardGammaType):
						# Get display profile vcgt
						vcgt_values = profile.tags.vcgt.get_values()[:3]
					if len(vcgt_values[0]) != 256:
						# Hmm. Do we need to deal with this?
						# I've never seen table-based vcgt with != 256 entries
						if self._force_reload and profile.tags.get("vcgt"):
							safe_print(lang.getstr("calibration.loading_from_display_profile"))
							safe_print(display)
							safe_print(lang.getstr("vcgt.unknown_format",
												   os.path.basename(profile.fileName)))
							safe_print(lang.getstr("failure"))
							results.append(display)
							errors.append(lang.getstr("vcgt.unknown_format",
													  os.path.basename(profile.fileName)))
						# Fall back to linear calibration
						tagData = "vcgt"
						tagData += "\0" * 4  # Reserved
						tagData += "\0\0\0\x01"  # Formula type
						for channel in xrange(3):
							tagData += "\0\x01\0\0"  # Gamma 1.0
							tagData += "\0" * 4  # Min 0.0
							tagData += "\0\x01\0\0"  # Max 1.0
						vcgt = ICCP.VideoCardGammaFormulaType(tagData, "vcgt")
						vcgt_values = vcgt.get_values()[:3]
					values = ([], [], [])
					if not self._force_reload:
						# Get video card gamma ramp
						hdc = win32gui.CreateDC(moninfo["Device"], None, None)
						ramp = ((ctypes.c_ushort * 256) * 3)()
						try:
							result = self.gdi32.GetDeviceGammaRamp(hdc, ramp)
						except:
							continue
						finally:
							win32gui.DeleteDC(hdc)
						if not result:
							continue
						# Get ramp values
						for j, channel in enumerate(ramp):
							for k, v in enumerate(channel):
								values[j].append([float(k), v])
					# Check if video card matches profile vcgt
					if values == vcgt_values:
						continue
					# Reload calibration.
					# Convert vcgt to ushort_Array_256_Array_3
					vcgt_ramp = ((ctypes.c_ushort * 256) * 3)()
					for j in xrange(len(vcgt_values[0])):
						for k in xrange(3):
							vcgt_ramp[k][j] = vcgt_values[k][j][1]
					if not self._force_reload:
						safe_print(lang.getstr("vcgt.mismatch", display))
					# Try and prevent race condition with madVR
					# launching and resetting video card gamma table
					apply_profiles = self._should_apply_profiles(first_run)
					if not apply_profiles:
						break
					# Now actually reload calibration
					safe_print(lang.getstr("calibration.loading_from_display_profile"))
					safe_print(display, "->", os.path.basename(profile.fileName))
					hdc = win32gui.CreateDC(moninfo["Device"], None, None)
					try:
						result = self.gdi32.SetDeviceGammaRamp(hdc, vcgt_ramp)
					except Exception, exception:
						result = exception
					finally:
						win32gui.DeleteDC(hdc)
					if isinstance(result, Exception) or not result:
						if result:
							safe_print(result)
						safe_print(lang.getstr("failure"))
						errstr = lang.getstr("calibration.load_error")
						errors.append(": ".join([display, errstr]))
					else:
						safe_print(lang.getstr("success"))
						results.append(display)
					##self.lock.release()
					##self.apply_profiles(True, index=i)
					##self.lock.acquire()
				##self.lock.release()
			self._force_reload = False
			first_run = False
			timestamp = time.time()
			localtime = list(time.localtime(self._timestamp))
			localtime[3:6] = 23, 59, 59
			midnight = time.mktime(localtime) + 1
			if timestamp >= midnight:
				self.reload_count = 0
				self._timestamp = timestamp
			if results or errors:
				self.notify(results, errors)
			else:
				if displaycal_running != self._displaycal_running:
					if displaycal_running:
						msg = lang.getstr("app.disconnected.calibration_loading_enabled",
										  appname)
					else:
						msg = lang.getstr("app.connected.calibration_loading_disabled",
										  appname)
					displaycal_running = self._displaycal_running
					safe_print(msg)
					self.notify([], [msg], displaycal_running)
			# Wait three seconds
			timeout = 0
			while wx.GetApp():
				time.sleep(.1)
				timeout += .1
				if timeout > 2.9 or self._force_reload:
					break
		self._reset_display_profile_associations()

	def _enumerate_monitors(self):
		import localization as lang
		from util_str import safe_unicode
		from util_win import (get_active_display_device,
							  get_real_display_devices_info)
		from edid import get_edid
		self.monitors = []
		for i, moninfo in enumerate(get_real_display_devices_info()):
			# Get monitor descriptive string
			device = get_active_display_device(moninfo["Device"])
			if device:
				display = safe_unicode(device.DeviceString)
			else:
				display = lang.getstr("unknown")
			try:
				edid = get_edid(i)
			except:
				edid = {}
			display = edid.get("monitor_name", display)
			m_left, m_top, m_right, m_bottom = moninfo["Monitor"]
			m_width = m_right - m_left
			m_height = m_bottom - m_top
			display = " @ ".join([display, 
								  "%i, %i, %ix%i" %
								  (m_left, m_top, m_width,
								   m_height)])
			self.monitors.append((display, moninfo))

	def _enumerate_windows_callback(self, hwnd, extra):
		import win32gui
		cls = win32gui.GetClassName(hwnd)
		if cls == "madHcNetQueueWindow":
			import pywintypes
			import win32api
			import win32con
			import win32process
			try:
				thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
				handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION |
											  win32con.PROCESS_VM_READ, False,
											  pid)
				name = win32process.GetModuleFileNameEx(handle, 0)
				win32api.CloseHandle(handle)
			except pywintypes.error:
				return
			if os.path.basename(name).lower() not in ("madhcctrl.exe",
													  "python.exe"):
				self.__madvr_isrunning = True

	def _is_madvr_running(self, fallback=False):
		""" Determine id madVR is in use (e.g. video playback, madTPG) """
		if sys.platform != "win32":
			return
		if len(self._madvr_instances):
			return True
		if fallback or not hasattr(self, "madvr"):
			# At launch, we won't be able to determine if madVR is running via
			# the callback API.
			import pywintypes
			import win32gui
			from log import safe_print
			self.__madvr_isrunning = False
			try:
				win32gui.EnumWindows(self._enumerate_windows_callback, None)
			except pywintypes.error, exception:
				safe_print(exception)
			return self.__madvr_isrunning

	def _madvr_connection_callback(self, param, connection, ip, pid, module,
								   component, instance, is_new_instance):
		with self.lock:
			import localization as lang
			from log import safe_print
			if ip in ("127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"):
				args = (param, connection, ip, pid, module, component, instance)
				if is_new_instance:
					apply_profiles = self._should_apply_profiles()
					self._madvr_instances.append(args)
					if apply_profiles:
						msg = lang.getstr("app.connected.calibration_loading_disabled",
										  component)
						safe_print(msg)
						self.notify([], [msg], True)
				elif args in self._madvr_instances:
					self._madvr_instances.remove(args)
					if self._should_apply_profiles():
						msg = lang.getstr("app.disconnected.calibration_loading_enabled",
										  component)
						safe_print(msg)
						self.notify([], [msg])

	def _reset_display_profile_associations(self):
		import ICCProfile as ICCP
		from log import safe_print
		for devicekey, (devicestring, profile) in self.devices2profiles.iteritems():
			if profile:
				try:
					current_profile = ICCP.get_display_profile(path_only=True,
															   devicekey=devicekey)
				except Exception, exception:
					safe_print(exception)
					continue
				if current_profile and current_profile != profile:
					safe_print("Resetting profile association for %s:" %
							   devicestring, current_profile, "->", profile)
					ICCP.set_display_profile(os.path.basename(profile),
											 devicekey=devicekey)

	def _set_display_profiles(self):
		import win32api

		import ICCProfile as ICCP
		from log import safe_print
		from util_win import get_active_display_device, get_display_devices
		self.devices2profiles = {}
		for i, (display, moninfo) in enumerate(self.monitors):
			for device in get_display_devices(moninfo["Device"]):
				try:
					profile = ICCP.get_display_profile(path_only=True,
													   devicekey=device.DeviceKey)
				except Exception, exception:
					safe_print(exception)
					profile = None
				self.devices2profiles[device.DeviceKey] = (device.DeviceString,
														   profile)
			# Set the active profile
			device = get_active_display_device(moninfo["Device"])
			if not device:
				continue
			try:
				correct_profile = ICCP.get_display_profile(path_only=True,
														   devicekey=device.DeviceKey)
			except Exception, exception:
				safe_print(exception)
				continue
			device = win32api.EnumDisplayDevices(moninfo["Device"], 0)
			current_profile = self.devices2profiles[device.DeviceKey][1]
			if correct_profile and current_profile != correct_profile:
				safe_print("Fixing profile association for %s:" % display,
						   current_profile, "->", correct_profile)
				ICCP.set_display_profile(os.path.basename(correct_profile),
										 devicekey=device.DeviceKey)

	def _set_force_reload(self, event):
		self._force_reload = True

	def _should_apply_profiles(self, first_run=False):
		import config
		from config import appbasename
		from util_win import calibration_management_isenabled
		displaycal_lockfile = os.path.join(config.confighome,
										   appbasename + ".lock")
		self._displaycal_running = os.path.isfile(displaycal_lockfile)
		return (("--force" in sys.argv[1:] or
				 (config.getcfg("profile.load_on_login") and
				  not calibration_management_isenabled())) and
				not self._displaycal_running and
				not self._is_madvr_running(first_run))

	def _toggle_fix_profile_associations(self, event):
		from config import setcfg
		setcfg("profile_loader.fix_profile_associations",
			   int(event.IsChecked()))
		if event.IsChecked():
			self._set_display_profiles()
		else:
			self._reset_display_profile_associations()


def main():
	unknown_option = None
	for arg in sys.argv[1:]:
		if arg not in ("--help", "--force", "--verify", "--silent",
					   "--error-dialog", "-V", "--version", "--skip"):
			unknown_option = arg
			break

	if "--help" in sys.argv[1:] or unknown_option:
		if unknown_option:
			print "%s: unrecognized option `%s'" % (os.path.basename(sys.argv[0]),
											 unknown_option)
		print "Usage: %s [OPTION]..." % os.path.basename(sys.argv[0])
		print "Apply profiles to configured display devices and load calibration"
		print "Version %s" % version
		print ""
		print "  --help           Output this help text and exit"
		print "  --force          Force loading of calibration/profile (if it has been"
		print "                   disabled in %s.ini)" % appname
		print "  --verify         Verify if calibration was loaded correctly"
		print "  --silent         Do not show dialog box on error"
		print "  --skip           Skip initial loading of calibration"
		print "  --error-dialog   Force dialog box on error"
		print "  -V, --version    Output version information and exit"
	elif "-V" in sys.argv[1:] or "--version" in sys.argv[1:]:
		print "%s %s" % (os.path.basename(sys.argv[0]), version)
	else:
		import config

		config.initcfg("apply-profiles")

		if (not "--force" in sys.argv[1:] and
			not config.getcfg("profile.load_on_login") and
			sys.platform != "win32"):
			# Early exit incase profile loading has been disabled and isn't forced
			sys.exit()

		if "--error-dialog" in sys.argv[1:]:
			config.setcfg("profile_loader.error.show_msg", 1)
			config.writecfg()

		import localization as lang
		lang.init()

		ProfileLoader()


if __name__ == "__main__":
	main()
