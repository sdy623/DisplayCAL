/*
 * Bootloader for a packed executable.
 * Copyright (C) 2005, Giovanni Bajo
 * Based on previous work under copyright (c) 2002 McMillan Enterprises, Inc.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * In addition to the permissions in the GNU General Public License, the
 * authors give you unlimited permission to link or embed the compiled
 * version of this file into combinations with other programs, and to
 * distribute those combinations without any restriction coming from the
 * use of this file. (The General Public License restrictions do apply in
 * other respects; for example, they cover modification of the file, and
 * distribution when not linked into a combine executable.)
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
 */
#include "launch.h"
#include <windows.h>
#include <commctrl.h> // InitCommonControls
#include <signal.h>

int relaunch(LPWSTR thisfile, char *workpath)
{
	char envvar[_MAX_PATH + 12];
	SECURITY_ATTRIBUTES sa;
	STARTUPINFOW si;
	PROCESS_INFORMATION pi;
	int rc = 0;

	// the parent process should ignore all signals it can
	signal(SIGABRT, SIG_IGN);
	signal(SIGINT, SIG_IGN);
	signal(SIGTERM, SIG_IGN);
	signal(SIGBREAK, SIG_IGN);

	VS("Setting up to run child\n");
	sa.nLength = sizeof(sa);
	sa.lpSecurityDescriptor = NULL;
	sa.bInheritHandle = TRUE;
	GetStartupInfoW(&si);
	si.lpReserved = NULL;
	si.lpDesktop = NULL;
	si.lpTitle = NULL;
	si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
	si.wShowWindow = SW_NORMAL;
	si.hStdInput = (void*)_get_osfhandle(fileno(stdin));
	si.hStdOutput = (void*)_get_osfhandle(fileno(stdout));
	si.hStdError = (void*)_get_osfhandle(fileno(stderr));
	/* tell pass 2 where we extracted to */
	VS("Setting magic environment var\n");
	strcpy(envvar, "_MEIPASS2=");
	strcat(envvar, workpath);
	_putenv(envvar);
	VS("Creating child process\n");
    // Use wide-string version to make sure that the command line is
    // passed properly: in fact, the locale-specific version (GetCommandLineA())
    // might not be able to decode it fully and thus contain replacement
    // characters ("?").
    // This is actually immaterial right now because Python itself has a bug
    // and uses only the locale-specific version which is corrupted; but at
    // least it's not here that we lose information.
	if (CreateProcessW( 
			thisfile, // pointer to name of executable module 
			GetCommandLineW(),  // pointer to command line string 
			&sa,  // pointer to process security attributes 
			NULL,  // pointer to thread security attributes 
			TRUE,  // handle inheritance flag 
			0,  // creation flags 
			NULL,  // pointer to new environment block 
			NULL,  // pointer to current directory name 
			&si,  // pointer to STARTUPINFO 
			&pi  // pointer to PROCESS_INFORMATION 
			)) {
		VS("Waiting for child process to finish...\n");
		WaitForSingleObject(pi.hProcess, INFINITE);
		GetExitCodeProcess(pi.hProcess, (unsigned long *)&rc);
	}
	else {
		FATALERROR("Error creating child process!\n");
		rc = -1;
	}
	return rc;
}


#ifdef _CONSOLE
int main(int argc, char* argv[])
#else
int APIENTRY WinMain( HINSTANCE hInstance, HINSTANCE hPrevInstance,
						LPSTR lpCmdLine, int nCmdShow )
#endif
{
	char here[_MAX_PATH + 1];
	char thisfile[_MAX_PATH + 1];
    WCHAR thisfilew[_MAX_PATH + 1];
	char pkgfile[_MAX_PATH + 1];
	int rc = 0;
	char *workpath = NULL;
	char *p;
	int len;
#ifndef _CONSOLE
	int argc = __argc;
	char **argv = __argv;
#endif

	// Initialize common controls (needed to link with commctrl32.dll and
	// obtain native XP look & feel).
	InitCommonControls();

	// fill in thisfile
	if (!GetModuleFileNameA(NULL, thisfile, _MAX_PATH)) {
		FATALERROR("System error - unable to load!");
		return -1;
	}
    if (!GetModuleFileNameW(NULL, thisfilew, _MAX_PATH)) {
        FATALERROR("System error - unable to load!");
        return -1;
    }

    p = thisfile+strlen(thisfile) - 4;
	if (strnicmp(p, ".exe", 4) != 0)
		strcat(thisfile, ".exe");

	// fill in here (directory of thisfile)
	//GetModuleFileName returns an absolute path
	strcpy(here, thisfile);
	for (p=here+strlen(here); *p != '\\' && p >= here+2; --p);
	*++p = '\0';
	len = p - here;

	strcpy(pkgfile, thisfile);
	strcpy(pkgfile+strlen(pkgfile)-3, "pkg");

	workpath = getenv( "_MEIPASS2" );
	rc = init(here, &thisfile[len], workpath);
	if (rc) {
		rc = init(here, &pkgfile[len], workpath);
		if (rc)
			return rc;
		VS("Found separate PKG: %s\n", pkgfile);
	} else {
		VS("Found embedded PKG: %s\n", thisfile);
	}
	if (workpath) {
		// we're the "child" process
		rc = doIt(argc, argv);
		if (rc) {
			return rc;
		}
		finalizePython();
	}
	else {
		if (extractBinaries(&workpath)) {
			VS("Error extracting binaries\n");
			return -1;
		}
		// if workpath got set to non-NULL, we've extracted stuff
		if (workpath) {
			// run the "child" process, then clean up
			rc = relaunch(thisfilew, workpath);
		}
		else {
			// no "child" process necessary
			rc = doIt(argc, argv);
			if (rc) {
				return rc;
			}
			finalizePython();
		}
		cleanUp();
	}
	return rc;
}
