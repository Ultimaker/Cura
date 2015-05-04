set -e
set -u

export OLD_PWD=`pwd`
export CMAKE=/c/software/PCL/cmake-3.0.1-win32-x86/bin/cmake.exe
export MAKE=mingw32-make.exe
export PATH=/c/mingw-w64/i686-4.9.2-posix-dwarf-rt_v3-rev1/mingw32/bin:$PATH

mkdir -p /c/software/protobuf/_build
cd /c/software/protobuf/_build
$CMAKE ../
$MAKE install

mkdir -p /c/software/libArcus/_build
cd /c/software/libArcus/_build
$CMAKE ../
$MAKE install

mkdir -p /c/software/PinkUnicornEngine/_build
cd /c/software/PinkUnicornEngine/_build
$CMAKE ../
$MAKE

cd $OLD_PWD
export PYTHONPATH=`pwd`/../libArcus/python:/c/Software/Uranium/
/c/python34/python setup.py py2exe

cp /c/software/PinkUnicornEngine/_build/CuraEngine.exe dist/
cp /c/software/libArcus/_install/bin/libArcus.dll dist/
cp /c/mingw-w64/i686-4.9.2-posix-dwarf-rt_v3-rev1/mingw32/bin/libgcc_s_dw2-1.dll dist/
cp /c/mingw-w64/i686-4.9.2-posix-dwarf-rt_v3-rev1/mingw32/bin/libwinpthread-1.dll dist/
cp /c/mingw-w64/i686-4.9.2-posix-dwarf-rt_v3-rev1/mingw32/bin/libstdc++-6.dll dist/

/c/program\ files\ \(x86\)/NSIS/makensis.exe installer.nsi
