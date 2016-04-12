#!/usr/bin/env bash

set -e
set -u

# This script is to package the Cura package for Windows/Linux and Mac OS X
# This script should run under Linux and Mac OS X, as well as Windows with Cygwin.

#############################
# CONFIGURATION
#############################

##Select the build target
BUILD_TARGET=${1:-none}
#BUILD_TARGET=win32
#BUILD_TARGET=darwin
#BUILD_TARGET=debian_i386
#BUILD_TARGET=debian_amd64
#BUILD_TARGET=debian_armhf
#BUILD_TARGET=freebsd

##Do we need to create the final archive
ARCHIVE_FOR_DISTRIBUTION=1
##Which version name are we appending to the final archive


##Version
version_file="./Cura/version"
while IFS= read -r line
do
    export BUILD_VERSION="$line"
done <"$version_file"
TARGET_DIR=Cura-${BUILD_VERSION}-${BUILD_TARGET}

##Git commit
GIT_HASH=$(git rev-parse --short=4 HEAD)

export FULL_VERSION=${BUILD_VERSION}-${GIT_HASH}

##Which versions of external programs to use
WIN_PORTABLE_PY_VERSION=2.7.2.1

##Which CuraEngine to use
if [ -z ${CURA_ENGINE_REPO:-} ] ; then
	CURA_ENGINE_REPO="https://code.alephobjects.com/diffusion/CE/curaengine.git"
fi

#############################
# Support functions
#############################
function checkTool
{
	if [ -z "`which $1`" ]; then
		echo "The $1 command must be somewhere in your \$PATH."
		echo "Fix your \$PATH or install $2"
		exit 1
	fi
}

function downloadURL
{
	filename=`basename "$1"`
	echo "Checking for $filename"
	if [ -f "$filename" ]; then
		FILE_SIZE=$(stat -c%s "$filename")
		SERVER_SIZE=$(curl -L -I "$1" | grep Content-Length | awk '{ sub(/\r$/,""); print $2}' | tail -n 1)
		echo "File $filename exists with $FILE_SIZE bytes. Server version has $SERVER_SIZE bytes"
		if [ "x$SERVER_SIZE" != "x" ]; then
			if [ "$SERVER_SIZE" -gt 0 ]; then
				if [ "$FILE_SIZE" -ne "$SERVER_SIZE" ]; then
					rm -f "$filename"
				fi
			fi
		fi
	fi
	if [ ! -f "$filename" ]; then
		echo "Downloading $1"
		curl -L -O "$1"
		if [ $? != 0 ]; then
			echo "Failed to download $1"
			exit 1
		fi
	fi
}

function extract
{
	echo "Extracting $*"
	echo "7z x -y $*" >> log.txt
	$EXTRACT x -y $* >> log.txt
	if [ $? != 0 ]; then
        echo "Failed to extract $*"
        exit 1
	fi
}

function gitClone
{
	echo "Cloning $1 into $2"
	if [ -d $2 ]; then
		cd $2
		git remote set-url origin $1
		git clean -dfx
		git reset --hard
		git pull
		cd -
	else
		git clone $1 $2
	fi
}

#############################
# Actual build script
#############################
if [ "$BUILD_TARGET" = "none" ]; then
	echo "You need to specify a build target with:"
	echo "$0 win32"
	echo "$0 debian_i386"
	echo "$0 debian_amd64"
	echo "$0 debian_armhf"
	echo "$0 darwin"
	echo "$0 freebsd"
	echo "$0 fedora                         # current   system"
	echo "$0 fedora \"mock_config_file\" ...  # different system(s)"
	exit 0
fi

if [ -z `which make` ]; then
	MAKE=mingw32-make
else
	MAKE=make
fi

if [ -z `which 7za` ]; then
	EXTRACT=7z
else
	EXTRACT=7za
fi

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

checkTool git "git: http://git-scm.com/"
checkTool curl "curl: http://curl.haxx.se/"
if [ $BUILD_TARGET = "win32" ]; then
	checkTool avr-gcc "avr-gcc: http://winavr.sourceforge.net/ "
	#Check if we have 7zip, needed to extract and packup a bunch of packages for windows.
	checkTool $EXTRACT "7zip: http://www.7-zip.org/"
	checkTool $MAKE "mingw: http://www.mingw.org/"
fi
#For building under MacOS we need gnutar instead of tar
if [ -z `which gnutar` ]; then
	TAR=tar
else
	TAR=gnutar
fi

#############################
# Build the required firmwares
#############################

gitClone "https://code.alephobjects.com/diffusion/CBD/cura-binary-data.git" _cura_binary_data

cp -v _cura_binary_data/cura/resources/firmware/* resources/firmware/

#############################
# Darwin
#############################

if [ "$BUILD_TARGET" = "darwin" ]; then
    TARGET_DIR=Cura-${BUILD_VERSION}-MacOS

	rm -rf scripts/darwin/build
	rm -rf scripts/darwin/dist

	python build_app.py py2app
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "Cannot build app."
		exit 1
	fi

    #Add cura version file (should read the version from the bundle with pyobjc, but will figure that out later)
    echo $BUILD_VERSION > scripts/darwin/dist/Cura.app/Contents/Resources/version
	rm -rf CuraEngine
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	$MAKE -C CuraEngine VERSION=${BUILD_VERSION}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	cp CuraEngine/build/CuraEngine scripts/darwin/dist/Cura.app/Contents/Resources/CuraEngine

	cd scripts/darwin

	# Install QuickLook plugin
	mkdir -p dist/Cura.app/Contents/Library/QuickLook
	cp -a STLQuickLook.qlgenerator dist/Cura.app/Contents/Library/QuickLook/

	# Archive app
	cd dist
	$TAR cfp - Cura.app | gzip --best -c > ../../../${TARGET_DIR}.tar.gz
	cd ..

	# Create sparse image for distribution
	hdiutil detach Cura_Volume || true
	rm -rf Cura.dmg.sparseimage
	hdiutil convert DmgTemplateCompressed.dmg -format UDSP -o Cura.dmg
	hdiutil resize -size 500m Cura.dmg.sparseimage
	hdiutil attach Cura.dmg.sparseimage -mountpoint Cura_Volume
	cp -a dist/Cura.app Cura_Volume/Cura/
	hdiutil detach Cura_Volume
	hdiutil convert Cura.dmg.sparseimage -format UDZO -imagekey zlib-level=9 -ov -o ../../Cura-${FULL_VERSION}-MacOS.dmg
	exit
fi

#############################
# FreeBSD part by CeDeROM
#############################

if [ "$BUILD_TARGET" = "freebsd" ]; then
	export CXX="c++"
	gitClone https://github.com/GreatFruitOmsk/Power Power
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	gmake -j4 -C CuraEngine VERSION=${BUILD_VERSION}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/freebsd/dist
	mkdir -p scripts/freebsd/dist/share/cura
	mkdir -p scripts/freebsd/dist/share/applications
	mkdir -p scripts/freebsd/dist/bin
	cp -a Cura scripts/freebsd/dist/share/cura/
	cp -a resources scripts/freebsd/dist/share/cura/
	cp -a plugins scripts/freebsd/dist/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/freebsd/dist/share/cura/
	cp scripts/freebsd/cura.py scripts/freebsd/dist/share/cura/
	cp scripts/freebsd/cura.desktop scripts/freebsd/dist/share/applications/
	cp scripts/freebsd/cura scripts/freebsd/dist/bin/
	cp -a Power/power scripts/freebsd/dist/share/cura/
	echo $BUILD_VERSION > scripts/freebsd/dist/share/cura/Cura/version
	#Create file list (pkg-plist)
	cd scripts/freebsd/dist
	find * -type f > ../pkg-plist
	DIRLVL=20; while [ $DIRLVL -ge 0 ]; do
		DIRS=`find share/cura -type d -depth $DIRLVL`
		for DIR in $DIRS; do
			echo "@dirrm $DIR" >> ../pkg-plist
		done
		DIRLVL=`expr $DIRLVL - 1`
	done
	cd ..
	# Create archive or package if root
	if [ `whoami` == "root" ]; then
	    echo "Are you root? Use the Port Luke! :-)"
	else
	    echo "You are not root, building simple package archive..."
	    pwd
	    $TAR czf ../../${TARGET_DIR}.tar.gz dist/**
	fi
	exit
fi

#############################
# Debian 32bit .deb
#############################

if [ "$BUILD_TARGET" = "debian_i386" ]; then
    export CXX="g++ -m32"
	gitClone https://github.com/GreatFruitOmsk/Power Power
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	$MAKE -C CuraEngine VERSION=${BUILD_VERSION}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/cura
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/cura
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp scripts/linux/cura.py scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a Power/power scripts/linux/${BUILD_TARGET}/usr/share/cura/
	echo $BUILD_VERSION > scripts/linux/${BUILD_TARGET}/usr/share/cura/Cura/version
	cat scripts/linux/debian_control | sed "s/\[BUILD_VERSION\]/${FULL_VERSION}/" | sed 's/\[ARCH\]/i386/' > scripts/linux/${BUILD_TARGET}/DEBIAN/control
	fakeroot sh -ec "
	 chown root:root scripts/linux/${BUILD_TARGET} -R
	 chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	 chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	 cd scripts/linux
	 dpkg-deb -Zgzip --build ${BUILD_TARGET} $(dirname ${TARGET_DIR})/cura_${FULL_VERSION}_i386.deb
	 chown `id -un`:`id -gn` ${BUILD_TARGET} -R
        "
	exit
fi

#############################
# Debian 64bit .deb
#############################

if [ "$BUILD_TARGET" = "debian_amd64" ]; then
    export CXX="g++ -m64"
	gitClone https://github.com/GreatFruitOmsk/Power Power
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	$MAKE -C CuraEngine VERSION=${BUILD_VERSION}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/cura
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/cura
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp scripts/linux/cura.py scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a Power/power scripts/linux/${BUILD_TARGET}/usr/share/cura/
	echo $BUILD_VERSION > scripts/linux/${BUILD_TARGET}/usr/share/cura/Cura/version
	cat scripts/linux/debian_control | sed "s/\[BUILD_VERSION\]/${FULL_VERSION}/" | sed 's/\[ARCH\]/amd64/' > scripts/linux/${BUILD_TARGET}/DEBIAN/control
	fakeroot sh -ec "
	 chown root:root scripts/linux/${BUILD_TARGET} -R
	 chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	 chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	 cd scripts/linux
	 dpkg-deb -Zgzip --build ${BUILD_TARGET} $(dirname ${TARGET_DIR})/cura_${FULL_VERSION}_amd64.deb
	 chown `id -un`:`id -gn` ${BUILD_TARGET} -R
	"
	exit
fi

#############################
# Debian armhf .deb
#############################

if [ "$BUILD_TARGET" = "debian_armhf" ]; then
    export CXX="g++"
	gitClone https://github.com/GreatFruitOmsk/Power Power
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	$MAKE -C CuraEngine VERSION=${BUILD_VERSION}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/cura
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/cura
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp scripts/linux/cura.py scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a Power/power scripts/linux/${BUILD_TARGET}/usr/share/cura/
	echo $BUILD_VERSION > scripts/linux/${BUILD_TARGET}/usr/share/cura/Cura/version
	cat scripts/linux/debian_control | sed "s/\[BUILD_VERSION\]/${FULL_VERSION}/" | sed 's/\[ARCH\]/armhf/' > scripts/linux/${BUILD_TARGET}/DEBIAN/control
	fakeroot sh -ec "
	 chown root:root scripts/linux/${BUILD_TARGET} -R
	 chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	 chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	 cd scripts/linux
	 dpkg-deb --build ${BUILD_TARGET} $(dirname ${TARGET_DIR})/Cura-${FULL_VERSION}-${BUILD_TARGET}.deb
	 chown `id -un`:`id -gn` ${BUILD_TARGET} -R
	"
	exit
fi

#############################
# Fedora Generic
#############################

function sanitiseVersion() {
  local _version="$1"
  echo "${_version//-/.}"
}

function fedoraCreateSRPM() {
  local _curaName="$1"
  local _version="$(sanitiseVersion "$2")"
  local _srcSpecFile="$3"
  local _srcSpecFileRelease="$4"
  local _dstSrpmDir="$5"

  local _dstTarSources="$HOME/rpmbuild/SOURCES/$_curaName-$_version.tar.gz"
  local _dstSpec="$HOME/rpmbuild/SPECS/$_curaName-$_version.spec"

  local _namePower="Power"
  local _nameCuraEngine="CuraEngine"

  gitClone "https://github.com/GreatFruitOmsk/Power" "$_namePower"
  gitClone "$CURA_ENGINE_REPO" "$_nameCuraEngine"

  cd "$_namePower"
  local _gitPower="$(git rev-list -1 HEAD)"
  cd -

  cd "$_nameCuraEngine"
  local _gitCuraEngine="$(git rev-list -1 HEAD)"
  cd -

  local _gitCura="$(git rev-list -1 HEAD)"

  rpmdev-setuptree

  rm -fv "$_dstTarSources"
  tar \
    --exclude-vcs \
    --transform "s#^#$_curaName-$_version/#" \
    -zcvf "$_dstTarSources" \
      "$_nameCuraEngine" \
      "$_namePower" \
      Cura \
      resources \
      plugins \
      scripts/linux/cura.py \
      scripts/linux/fedora/usr

  sed \
    -e "s#__curaName__#$_curaName#" \
    -e "s#__version__#$_version#" \
    -e "s#__gitCura__#$_gitCura#" \
    -e "s#__gitCuraEngine__#$_gitCuraEngine#" \
    -e "s#__gitPower__#$_gitPower#" \
    -e "s#__basedir__#scripts/linux/fedora#" \
    "$_srcSpecFile" \
    > "$_dstSpec"

  rpmbuild -bs "$_dstSpec"

  mkdir -pv "$_dstSrpmDir"
  cp -v \
    "$HOME/rpmbuild/SRPMS/$_curaName-$_version-$_srcSpecFileRelease.src.rpm" \
    "$_dstSrpmDir"
}

function buildFedora() {
  local _nameForRpm="Cura"
  local _versionForRpm="$(sanitiseVersion "$BUILD_VERSION")"

  #
  # SRPM
  #

  local _srcSpecFile="scripts/linux/fedora/rpm.spec"
  local _srcSpecFileRelease="$(rpmspec -P "$_srcSpecFile" | grep -E '^Release:'|awk '{print $NF}')"
  local _dstSrpmDir="scripts/linux/fedora/SRPMS"

  fedoraCreateSRPM \
    "$_nameForRpm" \
    "$_versionForRpm" \
    "$_srcSpecFile" \
    "$_srcSpecFileRelease" \
    "$_dstSrpmDir"

  #
  # RPM
  #

  local _srpmFile="$_dstSrpmDir/$_nameForRpm-$_versionForRpm-$_srcSpecFileRelease.src.rpm"
  local _dstRpmDir="scripts/linux/fedora/RPMS"

  while [ $# -ne 0 ]; do
    local _mockRelease="$(basename "${1%\.cfg}")"
    local _mockReleaseArg=""
    if [ -n "$_mockRelease" ]; then
      _mockReleaseArg="-r $_mockRelease"
    fi

    mkdir -pv "$_dstRpmDir/$_mockRelease"
    # Need to use /usr/bin/mock because depending on $PATH, if /usr/sbin/mock is
    # run instead, it will give an error.
    /usr/bin/mock \
      $_mockReleaseArg \
      --resultdir="$_dstRpmDir/$_mockRelease" \
      "$_srpmFile"

    shift 1
  done
}

#############################
# Fedora RPMs
#############################

if [ "$BUILD_TARGET" = "fedora" ]; then
  shift 1 # skip "fedora" arg

  if [ $# -eq 0 ]; then
    "$0" "$BUILD_TARGET" ""
  else
    buildFedora "${@}"
  fi

  exit
fi

#############################
# Rest
#############################

#############################
# Download all needed files.
#############################

if [ $BUILD_TARGET = "win32" ]; then
	#Get portable python for windows and extract it. (Linux and Mac need to install python themselfs)
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/PortablePython_${WIN_PORTABLE_PY_VERSION}.exe
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/PyOpenGL-3.0.1.win32.exe
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/VideoCapture-0.9-5.zip
	#downloadURL http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-20120927-git-13f0cd6-win32-static.7z
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/comtypes-0.6.2.win32.exe
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/ejectmedia.zip
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/wxPython3.0-win32-3.0.2.0.zip
	downloadURL http://devel.lulzbot.com/software/Cura/Build-Resources/pyserial-2.7.zip
	#Get the power module for python
	gitClone https://github.com/GreatFruitOmsk/Power Power
    if [ $? != 0 ]; then echo "Failed to clone Power"; exit 1; fi
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
fi

#############################
# Build the packages
#############################
rm -rf ${TARGET_DIR}
mkdir -p ${TARGET_DIR}

rm -f log.txt
if [ $BUILD_TARGET = "win32" ]; then
	if [ -z `which i686-w64-mingw32-g++` ]; then
		CXX=g++
	else
		CXX=i686-w64-mingw32-g++
	fi

	#In case we have left over files, we don't want the script to fail
	rm -rf App
	rm -rf PURELIB
	rm -rf VideoCapture-0.9-5
	rm -rf wxPython3.0-win32-3.0.2.0
	rm -rf pyserial-2.7
	rm -rf Win32
	
	#For windows extract portable python to include it.
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe App
	extract PyOpenGL-3.0.1.win32.exe PURELIB
	extract VideoCapture-0.9-5.zip VideoCapture-0.9-5/Python27/DLLs/vidcap.pyd
	#extract ffmpeg-20120927-git-13f0cd6-win32-static.7z ffmpeg-20120927-git-13f0cd6-win32-static/bin/ffmpeg.exe
	#extract ffmpeg-20120927-git-13f0cd6-win32-static.7z ffmpeg-20120927-git-13f0cd6-win32-static/licenses
	extract comtypes-0.6.2.win32.exe
	extract ejectmedia.zip Win32
	extract wxPython3.0-win32-3.0.2.0.zip
	extract pyserial-2.7.zip

	mkdir -p ${TARGET_DIR}/python
	mkdir -p ${TARGET_DIR}/Cura/
	mv App/Lib/site-packages/ PURELIB/
	mv App/* ${TARGET_DIR}/python

	mkdir -p ${TARGET_DIR}/python/Lib/site-packages/
	mv PURELIB/site-packages/setuptools* PURELIB/site-packages/site.py PURELIB/site-packages/easy_install.py ${TARGET_DIR}/python/Lib/site-packages/
	mv PURELIB/site-packages/numpy* ${TARGET_DIR}/python/Lib/site-packages/
	mv PURELIB/OpenGL ${TARGET_DIR}/python/Lib
	mv PURELIB/comtypes ${TARGET_DIR}/python/Lib
	mv pyserial-2.7/* ${TARGET_DIR}/python/Lib/site-packages/
	mv wxPython3.0-win32-3.0.2.0/* ${TARGET_DIR}/python/Lib/site-packages/
	mv Power/power ${TARGET_DIR}/python/Lib
	mv VideoCapture-0.9-5/Python27/DLLs/vidcap.pyd ${TARGET_DIR}/python/DLLs
	#mv ffmpeg-20120927-git-13f0cd6-win32-static/bin/ffmpeg.exe ${TARGET_DIR}/Cura/
	#mv ffmpeg-20120927-git-13f0cd6-win32-static/licenses ${TARGET_DIR}/Cura/ffmpeg-licenses/
	mv Win32/EjectMedia.exe ${TARGET_DIR}/Cura/
	cp -a scripts/win32/nsisPlugins/libgcc_s_dw2-1.dll ${TARGET_DIR}
	cp -a scripts/win32/nsisPlugins/libstdc++-6.dll ${TARGET_DIR}
	
	rm -rf Power/
	rm -rf App
	rm -rf PURELIB
	rm -rf VideoCapture-0.9-5
	rm -rf wxPython3.0-win32-3.0.2.0
	rm -rf pyserial-2.7
	#rm -rf ffmpeg-20120927-git-13f0cd6-win32-static

	#Clean up portable python a bit, to keep the package size down.
	rm -rf ${TARGET_DIR}/python/PyScripter.*
	rm -rf ${TARGET_DIR}/python/Doc
	rm -rf ${TARGET_DIR}/python/locale
	rm -rf ${TARGET_DIR}/python/tcl
	rm -rf ${TARGET_DIR}/python/Lib/test
	rm -rf ${TARGET_DIR}/python/Lib/distutils
	rm -rf ${TARGET_DIR}/python/Lib/site-packages/wx-3.0-msw/wx/tools
	rm -rf ${TARGET_DIR}/python/Lib/site-packages/wx-3.0-msw/wx/locale
	#Remove the gle files because they require MSVCR71.dll, which is not included. We also don't need gle, so it's safe to remove it.
	rm -rf ${TARGET_DIR}/python/Lib/OpenGL/DLLS/gle*

	# New in 2.7.6.1
	rm -rf ${TARGET_DIR}/python/PyCharm/
	rm -rf ${TARGET_DIR}/python/share/
	rm -rf ${TARGET_DIR}/python/qt.conf

	#Build the C++ engine
	$MAKE -C CuraEngine VERSION=${BUILD_VERSION} OS=Windows_NT CXX=${CXX}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
fi

#add Cura
mkdir -p ${TARGET_DIR}/Cura ${TARGET_DIR}/resources ${TARGET_DIR}/plugins
cp -a Cura/* ${TARGET_DIR}/Cura
cp -a resources/* ${TARGET_DIR}/resources
cp -a plugins/* ${TARGET_DIR}/plugins
#Add cura version file
echo $BUILD_VERSION > ${TARGET_DIR}/Cura/version

#add script files
if [ $BUILD_TARGET = "win32" ]; then
    cp -a scripts/win32/cura.bat $TARGET_DIR/
    cp CuraEngine/build/CuraEngine.exe $TARGET_DIR
    #cp /usr/lib/gcc/i686-w64-mingw32/4.8/libgcc_s_sjlj-1.dll $TARGET_DIR
    #cp /usr/i686-w64-mingw32/lib/libwinpthread-1.dll $TARGET_DIR
    #cp /usr/lib/gcc/i686-w64-mingw32/4.8/libstdc++-6.dll $TARGET_DIR
fi

#package the result
if (( ${ARCHIVE_FOR_DISTRIBUTION} )); then
	if [ $BUILD_TARGET = "win32" ]; then
		#rm ${TARGET_DIR}.zip
		#cd ${TARGET_DIR}
		#7z a ../${TARGET_DIR}.zip *
		#cd ..

		if [ ! -z `which wine` ]; then
			#if we have wine, try to run our nsis script.
			rm -rf scripts/win32/dist
			ln -sf `pwd`/${TARGET_DIR} scripts/win32/dist
			wine ~/.wine/drive_c/Program\ Files\ \(x86\)/NSIS/makensis.exe /DVERSION=${BUILD_VERSION} scripts/win32/installer.nsi
			if [ $? != 0 ]; then echo "Failed to package NSIS installer"; exit 1; fi
			mv scripts/win32/Cura_${FULL_VERSION}.exe ./
		fi
		if [ -f '/c/Program Files (x86)/NSIS/makensis.exe' ]; then
			rm -rf scripts/win32/dist
			mv "`pwd`/${TARGET_DIR}" scripts/win32/dist
			'/c/Program Files (x86)/NSIS/makensis.exe' -DVERSION=${BUILD_VERSION} 'scripts/win32/installer.nsi' >> log.txt
			if [ $? != 0 ]; then echo "Failed to package NSIS installer"; exit 1; fi
			mv scripts/win32/Cura_${BUILD_VERSION}.exe ./
		fi
	else
		echo "Archiving to ${TARGET_DIR}.tar.gz"
		$TAR cfp - ${TARGET_DIR} | gzip --best -c > ${TARGET_DIR}.tar.gz
	fi
else
	echo "Installed into ${TARGET_DIR}"
fi
