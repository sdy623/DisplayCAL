#!/bin/sh

dist=ubuntu9

platform=`uname -i`
version=`python -c "from dispcalGUI import meta;print meta.version"`

# Python 2.6 DEB
/usr/bin/python2.6 setup.py bdist_deb --cfg=$dist --use-distutils 2>&1 | tee dispcalGUI_$version-py2.6-$dist.$platform.bdist_deb.log
mv -f dist/dispcalgui_$version-1_$platform.deb dist/dispcalgui_$version-py2.6-$dist-1_$platform.deb
mv -f dist/dispcalGUI-$version-1.$platform.rpm dist/dispcalGUI-$version-py2.6-$dist-1.$platform.rpm
mv -f dist/dispcalGUI-$version-1.src.rpm dist/dispcalGUI-$version-py2.6-$dist-1.src.rpm
