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
export BUILD_NAME=15.01-RC8
TARGET_DIR=Cura-${BUILD_NAME}-${BUILD_TARGET}

##Which versions of external programs to use
WIN_PORTABLE_PY_VERSION=2.7.2.1

##Which CuraEngine to use
if [ -z ${CURA_ENGINE_REPO:-} ] ; then
	CURA_ENGINE_REPO="git@github.com:Ultimaker/CuraEngine.git"
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
	7z x -y $* >> log.txt
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

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

checkTool git "git: http://git-scm.com/"
checkTool curl "curl: http://curl.haxx.se/"
if [ $BUILD_TARGET = "win32" ]; then
	checkTool avr-gcc "avr-gcc: http://winavr.sourceforge.net/ "
	#Check if we have 7zip, needed to extract and packup a bunch of packages for windows.
	checkTool 7z "7zip: http://www.7-zip.org/"
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

if [ -d "C:/arduino-1.0.3" ]; then
	ARDUINO_PATH=C:/arduino-1.0.3
	ARDUINO_VERSION=103
elif [ -d "/Applications/Arduino.app/Contents/Resources/Java" ]; then
	ARDUINO_PATH=/Applications/Arduino.app/Contents/Resources/Java
	ARDUINO_VERSION=105
else
	ARDUINO_PATH=/usr/share/arduino
	ARDUINO_VERSION=105
fi

if [ ! -d "$ARDUINO_PATH" ]; then
  echo "Arduino path '$ARDUINO_PATH' doesn't exist"
  exit 1
fi


#Build the Ultimaker Original firmwares.
gitClone git@github.com:Ultimaker/Marlin.git _UltimakerMarlin
cd _UltimakerMarlin/Marlin
git checkout Marlin_v1
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_250000 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"250000_single\"' BAUDRATE=250000 TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_115200 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"115200_single\"' BAUDRATE=115200 TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_Dual_250000 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"250000_dual\"' BAUDRATE=250000 TEMP_SENSOR_1=-1 EXTRUDERS=2"
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_Dual_115200 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"115200_dual\"' BAUDRATE=115200 TEMP_SENSOR_1=-1 EXTRUDERS=2"
git checkout Marlin_UM_HeatedBedUpgrade
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_HBK_250000 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"250000_single_HB\"' BAUDRATE=250000 TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_HBK_115200 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"115200_single_HB\"' BAUDRATE=115200 TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_HBK_Dual_250000 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"250000_dual_HB\"' BAUDRATE=250000 TEMP_SENSOR_1=-1 EXTRUDERS=2"
$MAKE -j 3 HARDWARE_MOTHERBOARD=7 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_HBK_Dual_115200 DEFINES="'VERSION_BASE=\"Ultimaker:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"115200_dual_HB\"' BAUDRATE=115200 TEMP_SENSOR_1=-1 EXTRUDERS=2"
git checkout Marlin_UM_Original_Plus
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_Plus_250000 DEFINES="'VERSION_BASE=\"Ultimaker+:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"250000_single\"' BAUDRATE=250000 TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_Plus_115200 DEFINES="'VERSION_BASE=\"Ultimaker+:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"115200_single\"' BAUDRATE=115200 TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_Plus_Dual_250000 DEFINES="'VERSION_BASE=\"Ultimaker+:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"250000_dual\"' BAUDRATE=250000 TEMP_SENSOR_1=20 EXTRUDERS=2"
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_UltimakerMarlin_Plus_Dual_115200 DEFINES="'VERSION_BASE=\"Ultimaker+:_${BUILD_NAME}\"' 'VERSION_PROFILE=\"115200_dual\"' BAUDRATE=115200 TEMP_SENSOR_1=20 EXTRUDERS=2"
cd -

gitClone git@github.com:Ultimaker/Ultimaker2Marlin.git _Ultimaker2Marlin
cd _Ultimaker2Marlin/Marlin
git checkout master
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_Ultimaker2 DEFINES="'STRING_CONFIG_H_AUTHOR=\"Version:_${BUILD_NAME}\"' TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_Ultimaker2Dual DEFINES="'STRING_CONFIG_H_AUTHOR=\"Version:_${BUILD_NAME}\"' TEMP_SENSOR_1=20 EXTRUDERS=2"
git checkout UM2go
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_Ultimaker2go DEFINES="'STRING_CONFIG_H_AUTHOR=\"Version:_${BUILD_NAME}go\"' TEMP_SENSOR_1=0 EXTRUDERS=1"
git checkout UM2extended
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_Ultimaker2extended DEFINES="'STRING_CONFIG_H_AUTHOR=\"Version:_${BUILD_NAME}ex\"' TEMP_SENSOR_1=0 EXTRUDERS=1"
$MAKE -j 3 HARDWARE_MOTHERBOARD=72 ARDUINO_INSTALL_DIR=${ARDUINO_PATH} ARDUINO_VERSION=${ARDUINO_VERSION} BUILD_DIR=_Ultimaker2extendedDual DEFINES="'STRING_CONFIG_H_AUTHOR=\"Version:_${BUILD_NAME}ex\"' TEMP_SENSOR_1=20 EXTRUDERS=2"
cd -

cp _UltimakerMarlin/Marlin/_UltimakerMarlin_250000/Marlin.hex resources/firmware/MarlinUltimaker-250000.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_115200/Marlin.hex resources/firmware/MarlinUltimaker-115200.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_Dual_250000/Marlin.hex resources/firmware/MarlinUltimaker-250000-dual.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_Dual_115200/Marlin.hex resources/firmware/MarlinUltimaker-115200-dual.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_HBK_250000/Marlin.hex resources/firmware/MarlinUltimaker-HBK-250000.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_HBK_115200/Marlin.hex resources/firmware/MarlinUltimaker-HBK-115200.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_HBK_Dual_250000/Marlin.hex resources/firmware/MarlinUltimaker-HBK-250000-dual.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_HBK_Dual_115200/Marlin.hex resources/firmware/MarlinUltimaker-HBK-115200-dual.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_Plus_250000/Marlin.hex resources/firmware/MarlinUltimaker-UMOP-250000.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_Plus_115200/Marlin.hex resources/firmware/MarlinUltimaker-UMOP-115200.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_Plus_Dual_250000/Marlin.hex resources/firmware/MarlinUltimaker-UMOP-250000-dual.hex
cp _UltimakerMarlin/Marlin/_UltimakerMarlin_Plus_Dual_115200/Marlin.hex resources/firmware/MarlinUltimaker-UMOP-115200-dual.hex
cp _Ultimaker2Marlin/Marlin/_Ultimaker2/Marlin.hex resources/firmware/MarlinUltimaker2.hex
cp _Ultimaker2Marlin/Marlin/_Ultimaker2Dual/Marlin.hex resources/firmware/MarlinUltimaker2-dual.hex
cp _Ultimaker2Marlin/Marlin/_Ultimaker2go/Marlin.hex resources/firmware/MarlinUltimaker2go.hex
cp _Ultimaker2Marlin/Marlin/_Ultimaker2extended/Marlin.hex resources/firmware/MarlinUltimaker2extended.hex
cp _Ultimaker2Marlin/Marlin/_Ultimaker2extendedDual/Marlin.hex resources/firmware/MarlinUltimaker2extended-dual.hex

#############################
# Darwin
#############################

if [ "$BUILD_TARGET" = "darwin" ]; then
    TARGET_DIR=Cura-${BUILD_NAME}-MacOS

	rm -rf scripts/darwin/build
	rm -rf scripts/darwin/dist

	python build_app.py py2app
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "Cannot build app."
		exit 1
	fi

    #Add cura version file (should read the version from the bundle with pyobjc, but will figure that out later)
    echo $BUILD_NAME > scripts/darwin/dist/Cura.app/Contents/Resources/version
	rm -rf CuraEngine
	gitClone ${CURA_ENGINE_REPO} CuraEngine
    if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	$MAKE -C CuraEngine VERSION=${BUILD_NAME}
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
	hdiutil detach /Volumes/Cura\ -\ Ultimaker/ || true
	rm -rf Cura.dmg.sparseimage
	hdiutil convert DmgTemplateCompressed.dmg -format UDSP -o Cura.dmg
	hdiutil resize -size 500m Cura.dmg.sparseimage
	hdiutil attach Cura.dmg.sparseimage
	cp -a dist/Cura.app /Volumes/Cura\ -\ Ultimaker/Cura/
	hdiutil detach /Volumes/Cura\ -\ Ultimaker
	hdiutil convert Cura.dmg.sparseimage -format UDZO -imagekey zlib-level=9 -ov -o ../../${TARGET_DIR}.dmg
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
	gmake -j4 -C CuraEngine VERSION=${BUILD_NAME}
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
	echo $BUILD_NAME > scripts/freebsd/dist/share/cura/Cura/version
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
	$MAKE -C CuraEngine VERSION=${BUILD_NAME}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/cura
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/cura
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp scripts/linux/cura.py scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a Power/power scripts/linux/${BUILD_TARGET}/usr/share/cura/
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/usr/share/cura/Cura/version
	cat scripts/linux/debian_control | sed "s/\[BUILD_NAME\]/${BUILD_NAME}/" | sed 's/\[ARCH\]/i386/' > scripts/linux/${BUILD_TARGET}/DEBIAN/control
	sudo chown root:root scripts/linux/${BUILD_TARGET} -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	cd scripts/linux
	dpkg-deb --build ${BUILD_TARGET} $(dirname ${TARGET_DIR})/cura_${BUILD_NAME}-${BUILD_TARGET}.deb
	sudo chown `id -un`:`id -gn` ${BUILD_TARGET} -R
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
	$MAKE -C CuraEngine VERSION=${BUILD_NAME}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/cura
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/cura
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp scripts/linux/cura.py scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a Power/power scripts/linux/${BUILD_TARGET}/usr/share/cura/
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/usr/share/cura/Cura/version
	cat scripts/linux/debian_control | sed "s/\[BUILD_NAME\]/${BUILD_NAME}/" | sed 's/\[ARCH\]/amd64/' > scripts/linux/${BUILD_TARGET}/DEBIAN/control
	sudo chown root:root scripts/linux/${BUILD_TARGET} -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	cd scripts/linux
	dpkg-deb --build ${BUILD_TARGET} $(dirname ${TARGET_DIR})/cura_${BUILD_NAME}-${BUILD_TARGET}.deb
	sudo chown `id -un`:`id -gn` ${BUILD_TARGET} -R
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
	$MAKE -C CuraEngine VERSION=${BUILD_NAME}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/cura
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/cura
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp scripts/linux/cura.py scripts/linux/${BUILD_TARGET}/usr/share/cura/
	cp -a Power/power scripts/linux/${BUILD_TARGET}/usr/share/cura/
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/usr/share/cura/Cura/version
	cat scripts/linux/debian_control | sed "s/\[BUILD_NAME\]/${BUILD_NAME}/" | sed 's/\[ARCH\]/armhf/' > scripts/linux/${BUILD_TARGET}/DEBIAN/control
	sudo chown root:root scripts/linux/${BUILD_TARGET} -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	cd scripts/linux
	dpkg-deb --build ${BUILD_TARGET} $(dirname ${TARGET_DIR})/cura_${BUILD_NAME}-${BUILD_TARGET}.deb
	sudo chown `id -un`:`id -gn` ${BUILD_TARGET} -R
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
  local _versionForRpm="$(sanitiseVersion "$BUILD_NAME")"

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
    mock \
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
	downloadURL http://ftp.nluug.nl/languages/python/portablepython/v2.7/PortablePython_${WIN_PORTABLE_PY_VERSION}.exe
	downloadURL http://sourceforge.net/projects/pyserial/files/pyserial/2.5/pyserial-2.5.win32.exe
	downloadURL http://sourceforge.net/projects/pyopengl/files/PyOpenGL/3.0.1/PyOpenGL-3.0.1.win32.exe
	downloadURL http://sourceforge.net/projects/numpy/files/NumPy/1.6.2/numpy-1.6.2-win32-superpack-python2.7.exe
	downloadURL http://videocapture.sourceforge.net/VideoCapture-0.9-5.zip
	#downloadURL http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-20120927-git-13f0cd6-win32-static.7z
	downloadURL http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe
	downloadURL http://www.uwe-sieber.de/files/ejectmedia.zip
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
	
	#For windows extract portable python to include it.
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe \$_OUTDIR/App
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe \$_OUTDIR/Lib/site-packages
	extract pyserial-2.5.win32.exe PURELIB
	extract PyOpenGL-3.0.1.win32.exe PURELIB
	extract numpy-1.6.2-win32-superpack-python2.7.exe numpy-1.6.2-sse2.exe
	extract numpy-1.6.2-sse2.exe PLATLIB
	extract VideoCapture-0.9-5.zip VideoCapture-0.9-5/Python27/DLLs/vidcap.pyd
	#extract ffmpeg-20120927-git-13f0cd6-win32-static.7z ffmpeg-20120927-git-13f0cd6-win32-static/bin/ffmpeg.exe
	#extract ffmpeg-20120927-git-13f0cd6-win32-static.7z ffmpeg-20120927-git-13f0cd6-win32-static/licenses
	extract comtypes-0.6.2.win32.exe
	extract ejectmedia.zip Win32

	mkdir -p ${TARGET_DIR}/python
	mkdir -p ${TARGET_DIR}/Cura/
	mv \$_OUTDIR/App/* ${TARGET_DIR}/python
	mv \$_OUTDIR/Lib/site-packages/wx* ${TARGET_DIR}/python/Lib/site-packages/
	mv PURELIB/serial ${TARGET_DIR}/python/Lib
	mv PURELIB/OpenGL ${TARGET_DIR}/python/Lib
	mv PURELIB/comtypes ${TARGET_DIR}/python/Lib
	mv PLATLIB/numpy ${TARGET_DIR}/python/Lib
	mv Power/power ${TARGET_DIR}/python/Lib
	mv VideoCapture-0.9-5/Python27/DLLs/vidcap.pyd ${TARGET_DIR}/python/DLLs
	#mv ffmpeg-20120927-git-13f0cd6-win32-static/bin/ffmpeg.exe ${TARGET_DIR}/Cura/
	#mv ffmpeg-20120927-git-13f0cd6-win32-static/licenses ${TARGET_DIR}/Cura/ffmpeg-licenses/
	mv Win32/EjectMedia.exe ${TARGET_DIR}/Cura/
	
	rm -rf Power/
	rm -rf \$_OUTDIR
	rm -rf PURELIB
	rm -rf PLATLIB
	rm -rf VideoCapture-0.9-5
	rm -rf numpy-1.6.2-sse2.exe
	#rm -rf ffmpeg-20120927-git-13f0cd6-win32-static

	#Clean up portable python a bit, to keep the package size down.
	rm -rf ${TARGET_DIR}/python/PyScripter.*
	rm -rf ${TARGET_DIR}/python/Doc
	rm -rf ${TARGET_DIR}/python/locale
	rm -rf ${TARGET_DIR}/python/tcl
	rm -rf ${TARGET_DIR}/python/Lib/test
	rm -rf ${TARGET_DIR}/python/Lib/distutils
	rm -rf ${TARGET_DIR}/python/Lib/site-packages/wx-2.8-msw-unicode/wx/tools
	rm -rf ${TARGET_DIR}/python/Lib/site-packages/wx-2.8-msw-unicode/wx/locale
	#Remove the gle files because they require MSVCR71.dll, which is not included. We also don't need gle, so it's safe to remove it.
	rm -rf ${TARGET_DIR}/python/Lib/OpenGL/DLLS/gle*

    #Build the C++ engine
	$MAKE -C CuraEngine VERSION=${BUILD_NAME} OS=Windows_NT CXX=${CXX}
    if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
fi

#add Cura
mkdir -p ${TARGET_DIR}/Cura ${TARGET_DIR}/resources ${TARGET_DIR}/plugins
cp -a Cura/* ${TARGET_DIR}/Cura
cp -a resources/* ${TARGET_DIR}/resources
cp -a plugins/* ${TARGET_DIR}/plugins
#Add cura version file
echo $BUILD_NAME > ${TARGET_DIR}/Cura/version

#add script files
if [ $BUILD_TARGET = "win32" ]; then
    cp -a scripts/${BUILD_TARGET}/*.bat $TARGET_DIR/
    cp CuraEngine/build/CuraEngine.exe $TARGET_DIR
	cp /usr/lib/gcc/i686-w64-mingw32/4.8/libgcc_s_sjlj-1.dll $TARGET_DIR
    cp /usr/i686-w64-mingw32/lib/libwinpthread-1.dll $TARGET_DIR
    cp /usr/lib/gcc/i686-w64-mingw32/4.8/libstdc++-6.dll $TARGET_DIR
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
			wine ~/.wine/drive_c/Program\ Files\ \(x86\)/NSIS/makensis.exe /DVERSION=${BUILD_NAME} scripts/win32/installer.nsi
            if [ $? != 0 ]; then echo "Failed to package NSIS installer"; exit 1; fi
			mv scripts/win32/Cura_${BUILD_NAME}.exe ./
		fi
		if [ -f '/c/Program Files (x86)/NSIS/makensis.exe' ]; then
			rm -rf scripts/win32/dist
			mv "`pwd`/${TARGET_DIR}" scripts/win32/dist
			'/c/Program Files (x86)/NSIS/makensis.exe' -DVERSION=${BUILD_NAME} 'scripts/win32/installer.nsi' >> log.txt
            if [ $? != 0 ]; then echo "Failed to package NSIS installer"; exit 1; fi
			mv scripts/win32/Cura_${BUILD_NAME}.exe ./
		fi
	else
		echo "Archiving to ${TARGET_DIR}.tar.gz"
		$TAR cfp - ${TARGET_DIR} | gzip --best -c > ${TARGET_DIR}.tar.gz
	fi
else
	echo "Installed into ${TARGET_DIR}"
fi
