#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

dispcalGUI setup.py script

Can be used with setuptools or pure distutils (the latter can be forced
with the --use-distutils option, otherwise it will try to use setuptools by
default).

Also supported in addition to standard distutils/setuptools commands, are the 
bdist_bbfreeze, py2app and py2exe commands (if the appropriate packages are 
installed), which makes this file your all-around building/bundling powerhouse 
for dispcalGUI. In the case of py2exe, special care is taken of Python 2.6+ 
and the Microsoft.VC90.CRT assembly dependency, so if building an executable 
on Windows with Python 2.6+ you should preferably use py2exe. Please note that 
bdist_bbfreeze and py2app *require* setuptools.

IMPORTANT NOTE:
If called from within the installed package, should only be used to uninstall
(setup.py uninstall --record=INSTALLED_FILES), otherwise use the wrapper script
in the root directory of the source tar.gz/zip

"""

from distutils.command.install import install
from distutils.util import change_root, get_platform
import distutils.core
import glob
import os
import shutil
import sys
from types import StringType

from meta import author, author_ascii, description, domain, name, version, version_tuple
from relpath import relpath

pypath = os.path.abspath(__file__)
pydir = os.path.dirname(pypath)
basedir = os.path.dirname(pydir)

def setup():

	print "***", os.path.abspath(sys.argv[0]), " ".join(sys.argv[1:])

	bdist_bbfreeze = "bdist_bbfreeze" in sys.argv[1:]
	bdist_win = "bdist_msi" in sys.argv[1:] or "bdist_wininst" in sys.argv[1:]
	debug = 0
	do_full_install = False
	do_install = False
	do_py2app = "py2app" in sys.argv[1:]
	do_py2exe = "py2exe" in sys.argv[1:]
	do_uninstall = "uninstall" in sys.argv[1:]
	dry_run = "-n" in sys.argv[1:] or "--dry-run" in sys.argv[1:]
	install_data = None # data files install path (only if given)
	is_rpm_build = os.path.abspath(sys.argv[0]).endswith(os.path.join(os.path.sep, "rpm", "BUILD", name + "-" + version, os.path.basename(os.path.abspath(sys.argv[0]))))
	recordfile_name = None # record installed files to this file
	setuptools = None
	skip_instrument_conf_files = "--skip-instrument-configuration-files" in sys.argv[1:]
	use_distutils = not bdist_bbfreeze and not do_py2app and ("--use-distutils" in sys.argv[1:] or os.path.exists("use-distutils"))
	use_setuptools = bdist_bbfreeze or do_py2app or "--use-setuptools" in sys.argv[1:] or not use_distutils

	sys.path.insert(1, os.path.join(os.path.dirname(pydir), "util"))

	if not use_setuptools and use_distutils:
		if "--use-distutils" in sys.argv[1:] and not os.path.exists("use-distutils"):
			open("use-distutils", "w").close()
	else:
		if os.path.exists("use-distutils"):
			os.remove("use-distutils")
		try:
			from ez_setup import use_setuptools as ez_use_setuptools
			ez_use_setuptools()
		except ImportError:
			pass
		try:
			from setuptools import setup, Extension
			setuptools = True
			print "using setuptools"
		except ImportError:
			pass

	if not setuptools:
		from distutils.core import setup, Extension
		print "using distutils"
	
	if do_py2exe:
		# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
		try:
			# if this doesn't work, try import modulefinder
			import py2exe.mf as modulefinder
			import win32com
			for p in win32com.__path__[1:]:
				modulefinder.AddPackagePath("win32com", p)
			for extra in ["win32com.shell"]:
				__import__(extra)
				m = sys.modules[extra]
				for p in m.__path__[1:]:
					modulefinder.AddPackagePath(extra, p)
		except ImportError:
			# no build path setup, no worries.
			pass
	
	try:
		import py2exe
	except ImportError:
		if do_py2exe:
			raise
	
	if do_py2exe:
		origIsSystemDLL = py2exe.build_exe.isSystemDLL
		def isSystemDLL(pathname):
			if os.path.basename(pathname).lower() in ("gdiplus.dll", "mfc90.dll"):
				return 0
			return origIsSystemDLL(pathname)
		py2exe.build_exe.isSystemDLL = isSystemDLL

	if do_uninstall:
		i = sys.argv.index("uninstall")
		sys.argv = sys.argv[:i] + ["install"] + sys.argv[i + 1:]
		install.create_home_path = lambda self: None

	if skip_instrument_conf_files:
		i = sys.argv.index("--skip-instrument-configuration-files")
		sys.argv = sys.argv[:i] + sys.argv[i + 1:]

	if "--use-distutils" in sys.argv[1:]:
		i = sys.argv.index("--use-distutils")
		sys.argv = sys.argv[:i] + sys.argv[i + 1:]

	if "--use-setuptools" in sys.argv[1:]:
		i = sys.argv.index("--use-setuptools")
		sys.argv = sys.argv[:i] + sys.argv[i + 1:]

	for i in range(len(sys.argv[1:])):
		arg = sys.argv[i + 1]
		if arg in ("install", "install_lib", "install_headers", "install_scripts", "install_data"):
			if arg == "install":
				do_full_install = True
			do_install = True
		elif arg == "-d" and len(sys.argv[1:]) > i:
			dist_dir = sys.argv[i + 2]
		else:
			arg = arg.split("=")
			if len(arg) == 2:
				if arg[0] == "--dist-dir":
					dist_dir = arg[1]
				elif arg[0] == "--install-data":
					install_data = arg[1]
				elif arg[0] == "--record":
					recordfile_name = arg[1]

	if not recordfile_name and (do_full_install or do_uninstall):
		recordfile_name = "INSTALLED_FILES"
		# if not do_uninstall:
			# sys.argv.append("--record=" + "INSTALLED_FILES")

	if sys.platform in ("darwin", "win32") or "bdist_egg" in sys.argv[1:]:
		doc = data = "." if do_py2app or do_py2exe or bdist_bbfreeze else name
		if do_py2app:
			# dispcalGUI.app/Contents/Resources
			doc = os.path.join("..", "..", "..")
	else:
		# Linux/Unix
		data = name
		if "bdist_rpm" in sys.argv[1:] or is_rpm_build:
			doc = os.path.join("doc", "packages", name)
		else:
			doc = os.path.join("doc", name)
		if not install_data:
			data = os.path.join("share", data)
			doc = os.path.join("share", doc)
			if "bdist_rpm" in sys.argv[1:] or is_rpm_build:
				doc = os.path.join(os.path.sep, "usr", doc)

	# on Mac OS X and Windows, we want data files in the package dir
	# (package_data will be ignored when using py2exe)
	package_data = {
		name: [
			"lang/*.json",
			"presets/*.icc",
			"theme/*.png",
			"theme/icons/16x16/*.png",
			"theme/icons/22x22/*.png",
			"theme/icons/24x24/*.png",
			"theme/icons/32x32/*.png",
			"theme/icons/48x48/*.png",
			"theme/icons/256x256/*.png",
			"ti1/*.ti1",
			"test.cal"
		] if sys.platform in ("darwin", "win32") and not do_py2app and not do_py2exe else []
	}
	if sys.platform == "win32" and not do_py2exe:
		package_data[name] += ["theme/icons/*.ico"]
	data_files = [
		(os.path.join(doc, "screenshots"), 
			[os.path.join(pydir, "..", "screenshots", os.path.basename(fname)) for fname in 
			glob.glob(os.path.join(pydir, "..", "screenshots", "*.png"))]),
		(os.path.join(doc, "theme"), 
			[os.path.join(pydir, "..", "theme", "header-readme.png")]), 
		(os.path.join(doc, "theme", "icons"), 
			[os.path.join(pydir, "..", "theme", "icons", "favicon.ico")]), 
		(doc, [os.path.join(pydir, "..", "LICENSE.txt")]),
		(doc, [os.path.join(pydir, "..", "README.html")])
	] if not "bdist_rpm" in sys.argv[1:] and not is_rpm_build else []
	if sys.platform not in ("darwin", "win32") or do_py2app or do_py2exe:
		# Linux/Unix or py2app/py2exe
		data_files += [
			(os.path.join(data, "lang"), 
				[os.path.join(pydir, "lang", os.path.basename(fname)) for fname in 
				glob.glob(os.path.join(pydir, "lang", "*.json"))]), 
			(os.path.join(data, "presets"), 
				[os.path.join(pydir, "presets", os.path.basename(fname)) for fname in 
				glob.glob(os.path.join(pydir, "presets", "*.icc"))]),
			(os.path.join(data, "theme"), 
				[os.path.join(pydir, "theme", os.path.basename(fname)) for fname in 
				glob.glob(os.path.join(pydir, "theme", "*.png"))]), 
			(os.path.join(data, "ti1"), 
				[os.path.join(pydir, "ti1", os.path.basename(fname)) for fname in 
				glob.glob(os.path.join(pydir, "ti1", "*.ti1"))]),
			(data, [os.path.join(pydir, "test.cal")])
		]
		if sys.platform == "win32":
			if py2exe:
				data_files += [(os.path.join(data, "theme", "icons"), 
					[os.path.join(pydir, "theme", "icons", name + "-uninstall.ico")])]
			else:
				data_files += [(os.path.join(data, "theme", "icons"), 
					[os.path.join(pydir, "theme", "icons", os.path.basename(fname)) for fname in 
					glob.glob(os.path.join(pydir, "theme", "icons", "*.icns|*.ico"))])]
		elif sys.platform != "darwin" and not skip_instrument_conf_files:
			# Linux
			data_files += [(data, [os.path.join(pydir, "..", "misc", name + ".desktop")])]
			# device configuration / permission stuff
			devconf_files = []
			if os.path.isdir("/usr/share/PolicyKit/policy") and os.path.isdir("/usr/share/hal/fdi/policy/10osvendor"):
				# USB and Serial access using PolicyKit V0.6 + HAL (recent versions of Linux)
				devconf_files += [
					("/usr/share/PolicyKit/policy", [os.path.join(pydir, "..", "misc", "color-device-file.policy")]),
					("/usr/share/hal/fdi/policy/10osvendor", [os.path.join(pydir, "..", "misc", "19-color.fdi")])
				]
			if os.path.isdir("/etc/udev/rules.d"):
				if glob.glob("/dev/bus/usb/*/*"):
					# USB and serial instruments using udev, where udev already creates /dev/bus/usb/00X/00X devices
					devconf_files += [
						("/etc/udev/rules.d", [os.path.join(pydir, "..", "misc", "92-Argyll.rules")])
					]
				else:
					# USB using udev, where there are NOT /dev/bus/usb/00X/00X devices
					devconf_files += [
						("/etc/udev/rules.d", [os.path.join(pydir, "..", "misc", "45-Argyll.rules")])
					]
			else:
				if os.path.isdir("/etc/hotplug"):
					# USB using hotplug and Serial using udev (older versions of Linux)
					devconf_files += [
						("/etc/hotplug/usb", [os.path.join(pydir, "..", "misc", fname) for fname in ["Argyll", "Argyll.usermap"]])
					]
				if os.path.isdir("/etc/udev/permissions.d"):
					# Serial instruments using udev (older versions of Linux)
					devconf_files += [
						("/etc/udev/permissions.d", [os.path.join(pydir, "..", "misc", "10-Argyll.permissions")])
					]
			for entry in devconf_files:
				for fname in entry[1]:
					if os.path.isfile(fname):
						data_files += [(entry[0], [fname])]
		for dname in ("16x16", "22x22", "24x24", "32x32", "48x48", "256x256"):
			data_files += [(os.path.join(data, "theme", "icons", dname), 
				[os.path.join(pydir, "theme", "icons", dname, os.path.basename(fname)) for fname in 
				glob.glob(os.path.join(pydir, "theme", "icons", dname, "*.png"))])]

	if sys.platform == "win32":
		RealDisplaySizeMM = Extension(name + "." + "RealDisplaySizeMM", 
			sources = [os.path.join(name, "RealDisplaySizeMM.c")], 
			libraries = ["user32", "gdi32"], 
			define_macros=[("NT", None)])
	elif sys.platform == "darwin":
		RealDisplaySizeMM = Extension(name + "." + "RealDisplaySizeMM", 
			sources = [os.path.join(name, "RealDisplaySizeMM.c")],
			extra_link_args = ["-framework Carbon", "-framework Python", "-framework IOKit"], 
			define_macros=[("__APPLE__", None), ("UNIX", None)])
	else:
		RealDisplaySizeMM = Extension(name + "." + "RealDisplaySizeMM", 
			sources = [os.path.join(name, "RealDisplaySizeMM.c")], 
			libraries = ["Xinerama", "Xrandr", "Xxf86vm"], 
			define_macros=[("UNIX", None)])
	ext_modules = [RealDisplaySizeMM]

	requires = [
		"wxPython (>= 2.8.7)"
	]
	if sys.platform == "win32":
		requires += [
			"SendKeys (>= 0.3)",
			"pywin32 (>= 213.0)"
		]
	elif sys.platform == "darwin":
		requires += [
			"appscript (>= 0.19)"
		]
	else:
		pass

	attrs = {
		"author": author_ascii,
		"author_email": "%s@hoech.net" % name,
		"classifiers": [
			"Development Status :: 4 - Beta",
			"Environment :: Console",
			"Intended Audience :: End Users/Desktop",
			"Intended Audience :: Advanced End Users",
			"License :: OSI Approved :: GNU General Public License (GPL)",
			"Operating System :: OS Independent (Written in an interpreted language)",
			"Programming Language :: Python",
			"Topic :: Graphics",
			"User Interface :: Project is a user interface (UI) system",
			"User Interface :: wxWidgets",
		],
		"data_files": data_files,
		"description": description,
		"download_url": "http://%(name)s.hoech.net/%(name)s-%(version)s-src.zip" % 
			{"name": name, "version": version},
		"ext_modules": ext_modules,
		"license": "GPL v3",
		"long_description": description,
		"name": name,
		"packages": [name],
		"package_data": package_data,
		"package_dir": {
			name: name
		},
		"platforms": [
			"Python >= 2.5 < 3.0", 
			"Linux/Unix with X11", 
			"Mac OS X", 
			"Windows 2000 and newer"
		],
		"requires": requires,
		"scripts": [],
		"url": "http://%s.hoech.net/" % name,
		"version": ".".join(map(str, version_tuple)) if do_py2exe else version
	}

	if setuptools:
		attrs["entry_points"] = {
			"console_scripts": [
				"%s = %s.%s:main" % (name, name, name),
			]
		}
		attrs["exclude_package_data"] = {
			name: ["RealDisplaySizeMM.c"]
		}
		attrs["include_package_data"] = sys.platform in ("darwin", "win32")
		install_requires = [req.replace("(", "").replace(")", "") for req in requires]
		try:
			import wx
			if wx.__version__ >= "2.8.7":
				install_requires.remove("wxPython >= 2.8.7")
		except ImportError:
			pass
		attrs["install_requires"] = install_requires
		attrs["zip_safe"] = False
	else:
		attrs["scripts"] += [os.path.join("scripts", name)]
		# if sys.platform == "win32":
			# attrs["scripts"] += [os.path.join("scripts", name + ".cmd")]
	
	if bdist_bbfreeze:
		attrs["setup_requires"] = ["bbfreeze"]

	if bdist_win or setuptools:
		attrs["scripts"] += [os.path.join("util", name + "_postinstall.py")]
		
	if do_py2app:
		reversedomain = domain.split(".")
		reversedomain.reverse()
		reversedomain = ".".join(reversedomain)
		attrs["app"] = os.path.join(pydir, name + ".py"),
		attrs["options"] = {
			"py2app": {
				"argv_emulation": True,
				"dist_dir": os.path.join(pydir, "..", "dist", "py2app.%s-py%s" % (get_platform(), sys.version[:3]), name + "-" + version),
				"iconfile": os.path.join(pydir, "theme", "icons", "dispcalGUI.icns"),
				"optimize": 2,
				"plist": {
					"CFBundleDevelopmentRegion": "English",
					"CFBundleExecutable": name,
					"CFBundleGetInfoString": version,
					"CFBundleIdentifier": reversedomain,
					"CFBundleInfoDictionaryVersion": "6.0",
					"CFBundleLongVersionString": version,
					"CFBundleName": name,
					"CFBundlePackageType": "APPL",
					"CFBundleShortVersionString": version,
					"CFBundleSignature": "????",
					"CFBundleVersion": ".".join(map(str, version_tuple)),
					"NSHumanReadableCopyright": u"© " + author
				}
			}
		}
		attrs["setup_requires"] = ["py2app"]

	if do_py2exe:
		from winmanifest import getmanifestxml
		manifest_xml = getmanifestxml(os.path.join(pydir, "..", "misc", 
			name + (".exe.VC90.manifest" if hasattr(sys, "version_info") and 
			sys.version_info[:2] >= (2,6) else ".exe.manifest")))
		attrs["console"] = [{
			"script": os.path.join(pydir, name + ".py"),
			"icon_resources": [(1, os.path.join(pydir, "theme", "icons", name + ".ico"))],
			"other_resources": [(24, 1, manifest_xml)]
		}]
		dist_dir = os.path.join(pydir, "..", "dist", "py2exe.%s-py%s" % (get_platform(), sys.version[:3]), name + "-" + version)
		attrs["options"] = {
				"py2exe": {
						"dist_dir": dist_dir,
						"dll_excludes": [
							"iertutil.dll", 
							"msvcm90.dll", 
							"msvcp90.dll", 
							"msvcr90.dll", 
							"urlmon.dll",
							"w9xpopen.exe"
						],
						"bundle_files": 1,
						"compressed": 1,
						"optimize": 2
				}
		}
		if setuptools:
			attrs["setup_requires"] = ["py2exe"]
		attrs["zipfile"] = None

	if do_uninstall or do_install or bdist_win:
		distutils.core._setup_stop_after = "commandline"
		dist = setup(**attrs)
		distutils.core._setup_stop_after = None
		cmd = install(dist).get_finalized_command("install")
		if debug > 0:
			for attrname in [
				"base", 
				"data", 
				"headers", 
				"lib", 
				"libbase", 
				"platbase", 
				"platlib", 
				"prefix", 
				"purelib", 
				"root", 
				"scripts", 
				"userbase"
			]:
				if attrname not in ["prefix", "root"]:
					attrname = "install_" + attrname
				if hasattr(cmd, attrname):
					print attrname, getattr(cmd, attrname)
		if debug > 1:
			try:
				from ppdir import ppdir
			except ImportError:
				pass
			else:
				ppdir(cmd, types=[dict, list, str, tuple, type, unicode])
		if not install_data and sys.platform in ("darwin", "win32"):
			# on Mac OS X and Windows, we want data files in the package dir
			data_basedir = cmd.install_lib
		else:
			data_basedir = cmd.install_data
		data = change_root(data_basedir, data)
		doc = change_root(data_basedir, doc)
		# determine in which cases we want to make data file paths relative to site-packages (on Mac and Windows)
		# and when we want to make them absolute (Linux)
		linux = sys.platform not in ("darwin", "win32") and (not cmd.root and setuptools)
		dar_win = (sys.platform in ("darwin", "win32") and (cmd.root or not setuptools)) or bdist_win
		if not do_uninstall and not install_data and (linux or dar_win) and attrs["data_files"]:
			if data_basedir.startswith(cmd.install_data + os.path.sep):
				data_basedir = relpath(data_basedir, cmd.install_data)
			print "*** changing basedir for data_files:", data_basedir
			for i in range(len(attrs["data_files"])):
				f = attrs["data_files"][i]
				if type(f) is StringType:
					attrs["data_files"][i] = change_root(data_basedir, f)
				else:
					attrs["data_files"][i] = (change_root(data_basedir, f[0]), f[1])

	if do_uninstall:

		# quick and dirty uninstall

		if dry_run:
			print "dry run - nothing will be removed"
		else:
			from postinstall import postuninstall
			postuninstall(prefix=change_root(cmd.root, cmd.prefix) if cmd.root else cmd.prefix)
			# yeah, yeah - its actually pre-uninstall

		removed = []
		visited = []

		if os.path.exists(recordfile_name):
			paths = [(change_root(cmd.root, line.rstrip("\n")) if cmd.root else 
				line.rstrip("\n")) for line in open(recordfile_name, "r")]
		else:
			paths = []
		if not paths:
			# if the installed files have not been recorded, use some fallback logic to find them
			paths = glob.glob(os.path.join(cmd.install_scripts, name))
			if sys.platform == "win32":
				if setuptools:
					paths += glob.glob(os.path.join(cmd.install_scripts, name + ".exe"))
					paths += glob.glob(os.path.join(cmd.install_scripts, name + "-script.py"))
				else:
					paths += glob.glob(os.path.join(cmd.install_scripts, name + ".cmd"))
			paths += glob.glob(os.path.join(cmd.install_scripts, name + "_postinstall.py"))
			for attrname in [
				"data", 
				"headers", 
				"lib", 
				"libbase", 
				"platlib", 
				"purelib"
			]:
				path = os.path.join(getattr(cmd, "install_" + attrname), name)
				if not path in paths:
					paths += glob.glob(path) + glob.glob(path + 
						("-%(version)s-py%(pyversion)s*.egg" % {
							"version": version, 
							"pyversion": sys.version[:3] # using sys.version in this way is consistent with setuptools
						})
					) + glob.glob(path + 
						("-%(version)s-py%(pyversion)s*.egg-info" % {
							"version": version, 
							"pyversion": sys.version[:3] # using sys.version in this way is consistent with setuptools
						})
					)
			if os.path.isabs(data) and not data in paths:
				for fname in [
					"lang",
					"presets",
					"screenshots",
					"theme",
					"ti1",
					"LICENSE.txt",
					"README.html",
					name + ".desktop",
					"test.cal"
				]:
					path = os.path.join(data, fname)
					if not path in paths:
						paths += glob.glob(path)
			if os.path.isabs(doc) and not doc in paths:
				for fname in [
					"screenshots",
					"theme",
					"LICENSE.txt",
					"README.html"
				]:
					path = os.path.join(doc, fname)
					if not path in paths:
						paths += glob.glob(path)
			if sys.platform == "win32":
				from postinstall import get_special_folder_path
				startmenu_programs_common = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
				startmenu_programs = get_special_folder_path("CSIDL_PROGRAMS")
				for path in (startmenu_programs_common, startmenu_programs):
					if path:
						for filename in (name, "LICENSE", "README", "Uninstall"):
							paths += glob.glob(os.path.join(path, name, filename + ".lnk"))

		for path in paths:
			if os.path.exists(path):
				if path in visited:
					continue
				else:
					visited += [path]
				if dry_run:
					print path
					continue
				try:
					if os.path.isfile(path):
						os.remove(path)
					elif os.path.isdir(path):
						shutil.rmtree(path, False)
				except Exception, exception:
					print "could'nt remove", path
					print "   ", exception
				else:
					print "removed", path
					removed += [path]
			while path != os.path.dirname(path):
				# remove parent directories if empty
				# could also use os.removedirs(path) but we want some status info
				path = os.path.dirname(path)
				if os.path.isdir(path):
					if len(os.listdir(path)) == 0:
						if path in visited:
							continue
						else:
							visited += [path]
						if dry_run:
							print path
							continue
						try:
							os.rmdir(path)
						except Exception, exception:
							print "could'nt remove", path
							print "   ", exception
						else:
							print "removed", path
							removed += [path]
					else:
						break

		if not removed:
			print len(visited), "entries found"
		else:
			print len(removed), "entries removed"

	else:

		# To have a working sdist and bdist_rpm when using distutils,
		# we go to the length of generating MANIFEST.in from scratch everytime, 
		# using the information available from setup.
		manifest_in = ["# This file will be re-generated by setup.py - do not edit"]
		manifest_in += ["include LICENSE.txt", "include MANIFEST", "include MANIFEST.in", "include README.html", "include use-distutils"]
		manifest_in += ["include " + os.path.basename(sys.argv[0])]
		manifest_in += ["include " + os.path.splitext(os.path.basename(sys.argv[0]))[0] + ".cfg"]
		for datadir, datafiles in attrs.get("data_files", []):
			for datafile in datafiles:
				manifest_in += ["include " + relpath(os.path.sep.join(datafile.split("/")), basedir)]
		for extmod in attrs.get("ext_modules", []):
			manifest_in += ["include " + os.path.sep.join(src.split("/")) for src in extmod.sources]
		for pkg in attrs.get("packages", []):
			pkgdir = os.path.sep.join(attrs.get("package_dir", {}).get(pkg, pkg).split("/"))
			manifest_in += ["include " + os.path.join(pkgdir, "*.py")]
			for obj in attrs.get("package_data", {}).get(pkg, []):
				manifest_in += ["include " + os.path.sep.join([pkgdir] + obj.split("/"))]
		for pymod in attrs.get("py_modules", []):
			manifest_in += ["include " + os.path.join(*pymod.split("."))]
		manifest_in += ["include " + os.path.join("dispcalGUI", "theme", "theme-info.txt")]
		manifest_in += ["recursive-include %s %s %s" % (os.path.join("dispcalGUI", "theme", "icons"), "*.icns", "*.ico")]
		manifest_in += ["recursive-include %s %s" % ("autopackage", "*.apspec")]
		manifest_in += ["recursive-include %s %s" % ("misc", "*")]
		manifest_in += ["recursive-exclude %s %s" % ("misc", "warn%s-pyi-*.txt" % name)]
		if skip_instrument_conf_files:
			manifest_in += [
				"exclude misc/Argyll",
				"recursive-exclude misc *.fdi",
				"recursive-exclude misc *.permissions",
				"recursive-exclude misc *.policy",
				"recursive-exclude misc *.rules",
				"recursive-exclude misc *.usermap",
			]
		manifest_in += ["recursive-include %s %s" % ("pyinstaller", " ".join([
			"*.c",
			"*.cfg",
			"*.cmd",
			"*.conf",
			"*.config",
			"*.css",
			"*.def",
			"*.h",
			"*.html",
			"*.ico",
			"*.manifest",
			"*.png",
			"*.policy",
			"*.py",
			"*.rc",
			"*.rst",
			"*.sh",
			"*.spec",
			"*.tex",
			"*.txt",
			"*.vbs",
			"*.xml",
		]))]
		manifest_in += ["include " + os.path.join("pyinstaller", obj) for obj in [
			os.path.join("doc", "LICENSE.GPL"),
			os.path.join("doc", "source", "Makefile"),
			os.path.join("doc", "source", "tools", "README"),
			os.path.join("source", "Sconscript"),
			os.path.join("source", "zlib", "README"),
			os.path.join("support", "loader", "*.dll"),
			os.path.join("support", "loader", "*.exe"),
			".hgignore",
			"Sconstruct",
			"rthooks.dat",
		]]
		manifest_in += ["recursive-include %s %s" % ("screenshots", "*.png")]
		manifest_in += ["recursive-include %s %s" % ("scripts", "*")]
		manifest_in += ["recursive-include %s %s" % ("theme", "*")]
		manifest_in += ["recursive-include %s %s" % ("util", "*.cmd *.py *.sh")]
		if sys.platform == "win32" and not setuptools:
			manifest_in += ["global-exclude .svn/*"] # (only) needed under Windows
		manifest_in += ["global-exclude *~"]
		manifest = open("MANIFEST.in", "w")
		manifest.write("\n".join(manifest_in))
		manifest.close()
		if os.path.exists("MANIFEST"):
			os.remove("MANIFEST")

		if bdist_bbfreeze:
			i = sys.argv.index("bdist_bbfreeze")
			if not "-d" in sys.argv[i + 1:] and not "--dist-dir" in sys.argv[i + 1:]:
				dist_dir = os.path.join(pydir, "..", "dist", "bbfreeze.%s-py%s" % (get_platform(), sys.version[:3]))
				sys.argv.insert(i + 1, "--dist-dir=" + dist_dir)
			if not "egg_info" in sys.argv[1:i]:
				sys.argv.insert(i, "egg_info")

		if do_py2app or do_py2exe:
			sys.path.insert(1, pydir)
			i = sys.argv.index("py2app" if do_py2app else "py2exe")
			if not "build_ext" in sys.argv[1:i]:
				sys.argv.insert(i, "build_ext")
			if len(sys.argv) < i + 2 or sys.argv[i + 1] not in ("--inplace", "-i"):
				sys.argv.insert(i + 1, "-i")

		setup(**attrs)

		if ((bdist_bbfreeze and sys.platform == "win32") or do_py2exe) and sys.version_info[:2] >= (2,6):
			from vc90crt import name as vc90crt_name, vc90crt_copy_files
			vc90crt_copy_files(os.path.join(dist_dir, vc90crt_name) if do_py2exe else os.path.join(dist_dir, name + "-" + version))
		
		if "bdist_wininst" in sys.argv[1:]:
			exe = os.path.join("dist", name + (
				"-%(version)s.%(platform)s-py%(pyversion)s.exe" % 
				{
					"version": version, 
					"platform": get_platform(),
					"pyversion": sys.version[:3] # using sys.version in this way is consistent with setuptools
				}
			))
			# FIXME: exe gets truncated by UpdateResource
			# if os.path.exists(exe):
				# sys.path.insert(1, os.path.join(os.path.dirname(pydir), "pyinstaller"))
				
				# from icon import CopyIcons
				# from manifest import UpdateManifestResourcesFromXMLFile
				# from versionInfo import SetVersion
				# from winmanifest import mktempmanifest
				# from winversion import mktempver
				
				# manifest = mktempmanifest(os.path.join(pydir, "..", "misc", name + 
					# (".exe.VC90.manifest" if hasattr(sys, "version_info") and 
					# sys.version_info[:2] >= (2,6) else ".exe.manifest")))
				# version = mktempver(os.path.join(pydir, "..", "misc", "winversion.txt"))
				
				# CopyIcons(exe, os.path.join(pydir, "theme", "icons", name + ".ico"))
				# SetVersion(exe, version)
				# UpdateManifestResourcesFromXMLFile(exe, manifest)
				
				# os.remove(manifest)
				# os.rmdir(os.path.dirname(manifest))
				# os.remove(version)
				# os.rmdir(os.path.dirname(version))
		
		if not dry_run and do_full_install:
			from postinstall import postinstall
			if sys.platform == "win32":
				path = os.path.join(cmd.install_lib, name)
				for path in glob.glob(path) + glob.glob(
					os.path.join(path + (
						"-%(version)s-py%(pyversion)s*.egg" % 
						{
							"version": version, 
							"pyversion": sys.version[:3] # using sys.version in this way is consistent with setuptools
						}
					), name)
				):
					postinstall(prefix=change_root(cmd.root, path) if cmd.root else path)
			else:
				postinstall(prefix=change_root(cmd.root, cmd.prefix) if cmd.root else cmd.prefix)

if __name__ == "__main__":
	setup()
