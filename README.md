Cura
====

If you are reading this, then you are looking at the *development* version of Cura. If you just want to use Cura look at the following location: https://github.com/daid/Cura/wiki

Development
===========

Cura is developed in Python. Getting Cura up and running for development is not very difficult. If you copy the python and pypy from a release into your Cura development checkout then you can use Cura right away, just like you would with a release.
For development with git, check the help on github. Pull requests is the fastest way to get changes into Cura.


Packaging
---------

Cura development comes with a script "package.sh", this script has been designed to run under unix like OSes (Linux, MacOS). Running it from sygwin is not a priority.
The "package.sh" script generates a final release package. You should not need it during development, unless you are changing the release process. If you want to distribute your own version of Cura, then the package.sh script will allow you to do that.


Mac OS X
--------
The following section describes how to prepare working environment for developing and packaing for Mac OS X.
The working environment consist of build of Python, build of wxPython and all required Python packages.

We assume you already have Apple hardware with [64bit processor](http://support.apple.com/kb/HT3696) and you are familiar with tools like [virtualenv](http://pypi.python.org/pypi/virtualenv), [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) and [pip](http://www.pip-installer.org/en/latest/). Also ensure you have modern compiler installed.


###Install Python
You'll need **non-system**, **framework-based**, **universal** with **deployment target set to 10.6** build of Python 2.7

**non-system**: Python is not bundeled with distribution of Mac OS X. Output of  
`python -c "import sys; print sys.prefix"`  
Output should *not* start with *"/System/Library/Frameworks/Python.framework/"*.

**framework-based**: Output of  
`python -c "import distutils.sysconfig as c; print(c.get_config_var('PYTHONFRAMEWORK'))"`  
should be non-empty string.

**universal**: Output of  
``lipo -info `which python` ``  
should include both i386 and x86_64. E.g *"Architectures in the fat file: /usr/local/bin/python are: i386 x86_64"*.

**deployment target set to 10.6**: Output of  
``otool -l `which python` ``  
should contain *"cmd LC_VERSION_MIN_MACOSX ... version 10.6"*.

The easiest way to install it is via [Homebrew](http://mxcl.github.com/homebrew/):  
`brew install --fresh https://github.com/downloads/GreatFruitOmsk/Cura/python.rb --universal`  
Note if you already have Python installed via Homebrew, you have to uninstall it first.


###Configure Virtualenv
Create new virtualenv. If you have [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) installed:  
`mkvirtualenv Cura`

wxPython cannot be installed via pip, we have to build it from source by specifing prefix to our virtualenv.

Assuming you have virtualenv at *~/.virtualenvs/Cura/* and [wxPython sources](http://sourceforge.net/projects/wxpython/files/wxPython/2.9.4.0/wxPython-src-2.9.4.0.tar.bz2) at *~/Downloads/wxPython-src-2.9.4.0/*:

1. `cd` into *~/Downloads/wxPython-src-2.9.4.0/* and configure the sources:

        ./configure --enable-universal_binary=i386,x86_64 \
        --prefix=$HOME/.virtualenvs/Cura/ \
        --enable-optimise \
        --with-libjpeg=builtin \
        --with-libpng=builtin \
        --with-libtiff=builtin \
        --with-zlib=builtin \
        --enable-monolithic \
        --with-macosx-version-min=10.6 \
        --disable-debug \
        --enable-unicode \
        --enable-std_string \
        --enable-display \
        --with-opengl \
        --with-osx_cocoa \
        --enable-dnd \
        --enable-clipboard \
        --enable-webkit \
        --enable-svg \
        --with-expat

2. `make install`  
    Note to speedup the process I recommend you to enable multicore build by adding the -j*cores* flag:  
    `make -j4 install`
3. `cd` into *~/Downloads/wxPython-src-2.9.4.0/wxPython/*
4. Build wxPython (Note `python` is the python of your virtualenv):

        python setup.py build_ext \
        WXPORT=osx_cocoa \
        WX_CONFIG=$HOME/.virtualenvs/Cura/bin/wx-config \
        UNICODE=1 \
        INSTALL_MULTIVERSION=0 \
        BUILD_GLCANVAS=1 \
        BUILD_GIZMOS=1 \
        BUILD_STC=1

5. Install wxPython (Note `python` is the python of your virtualenv):

        python setup.py install \
        --prefix=$HOME/.virtualenvs/Cura/ \
        WXPORT=osx_cocoa \
        WX_CONFIG=$HOME/.virtualenvs/Cura/bin/wx-config \
        UNICODE=1 \
        INSTALL_MULTIVERSION=0 \
        BUILD_GLCANVAS=1 \
        BUILD_GIZMOS=1 \
        BUILD_STC=1

6. Create file *~/.virtualenvs/Cura/bin/pythonw* with the following content:

        #!/bin/bash
        ENV=`python -c "import sys; print sys.prefix"`
        PYTHON=`python -c "import sys; print sys.real_prefix"`/bin/python
        export PYTHONHOME=$ENV
        exec $PYTHON "$@"

At this point virtualenv is configured for wxPython development.  
Remember to use `python` for pacakging and `pythonw` to run app for debugging.


###Install Python Packages
Required python packages are specified in *requirements.txt* and *requirements_darwin.txt*  
If you use virtualenv, installing requirements as easy as `pip install -r requirements_darwin.txt`

At time of writing PyObjC 2.5 is not available via pip, so you have to install it manually (Note `python` is the python of your virtualenv):

1. Download [PyObjC 2.5](https://bitbucket.org/ronaldoussoren/pyobjc/get/pyobjc-2.5.zip)
2. Extract the archive and `cd` into the directory
3. `python install.py`  
    If build fails, try to use clang: `CC=/usr/bin/clang python install.py`


###Package Cure into application
Ensure that `package.sh` build target (see the very top of the file) is:

    #BUILD_TARGET=${1:-all}
    #BUILD_TARGET=win32
    #BUILD_TARGET=linux
    BUILD_TARGET=darwin

Also ensure that virtualenv is activated, so `python` points to the python of your virtualenv (e.g. ~/.virtualenvs/Cura/bin/python).


###Tests
Cura was built (and each build was tested) on the following platforms:

- 10.6.8
- 10.7.3
- 10.8.2
- 10.8.3 (Jan 8 Seed)

With following tools, libs and python pacakges:

- Python 2.7.3 (installed via [Homebrew](http://mxcl.github.com/homebrew/) by using custom [formula](https://github.com/downloads/GreatFruitOmsk/Cura/python.rb) with *--universal* option)
- [wxPython 2.9.4.0](http://sourceforge.net/projects/wxpython/files/wxPython/2.9.4.0/wxPython-src-2.9.4.0.tar.bz2)
- virtualenvwrapper 3.6
- vritualenv 1.8.4
- llvm-gcc 4.2 (/usr/bin/cc == /usr/bin/llvm-gcc-4.2)
- clang 2.1, 3.0 (PyObjC 2.5 failed to build with llvm-gcc)
- [PyObjC 2.5](https://bitbucket.org/ronaldoussoren/pyobjc/get/pyobjc-2.5.zip)
- PyOpenGL 3.0.2
- altgraph 0.10.1
- macholib 1.5
- modulegraph 0.10.2
- numpy 1.6.2
- py2app 0.7.2
- pyserial 2.6
- wsgiref 0.1.2
