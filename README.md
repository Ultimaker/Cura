Cura
====

Read this, it's important!
===========================

If you are reading this, then you are looking at the *development* version of Cura. If you just want to use Cura, take a look at the following location: https://daid.github.com/Cura

Development
===========

Cura is developed in Python with a C++ engine. The part you are looking at right now is the Python GUI.
The C++ engine is responsible for generating the actual toolpath. For development of the engine check out https://github.com/Ultimaker/CuraEngine

Issues
===========

Before posting issues (either Bugs, Feature requests or Requests for information) please read our policies carefully. These will be regulary updated and can be found at https://github.com/daid/Cura/wiki/Issue-policies


Packaging
---------

Cura development comes with a script "package.sh", this script has been designed to run under *nix OSes (Linux, MacOS, FreeBSD). For Windows the package.sh script can be run from bash using git.
The "package.sh" script generates a final release package. You should not need it during development, unless you are changing the release process. If you want to distribute your own version of Cura, then the package.sh script will allow you to do that.

Both MacOS and Linux require some extra instructions for development, as you need to prepare an environment. Look below at the proper section to see what is needed.

Fedora
--------

Fedora builds Cura by using ```mock```, thereby enabling it to build RPMs for
every distribution that ```mock``` has a configuration file for. In pratice
this means that Fedora can build RPMs for several versions of Fedora, CentOS
and RHEL.

Cura can be built under a regular user account, there is no need to have root
privileges. In fact, having root privileges is very much discouraged.

However, the user account under which the build is performed needs to be a
member of the 'mock' group. This is accomplished as follows:

```bash
sudo usermod -a -G mock "$(whoami)"
```

To install the software that is required to build Cura, run the following
commands:

```bash
sudo yum install -y git rpmdevtools rpm-build mock arduino

# Ensure that the Arduino tools can be found by the build
sudo mkdir -p /usr/share/arduino/hardware/tools/avr
sudo ln -sf /usr/bin /usr/share/arduino/hardware/tools/avr/bin

```

To build and install Cura, run the following commands:

```bash
# Get the Cura software, only required once
git clone https://github.com/daid/Cura.git Cura

# Build for the current system
cd Cura
./package.sh fedora

# Install on the current system
sudo yum localinstall -y scripts/linux/fedora/RPMS/Cura-*.rpm
```

Examples of building other configurations:

```bash
# Build for Fedora rawhide x86-64 and i386
./package.sh fedora fedora-rawhide-x86_64.cfg fedora-rawhide-i386.cfg

# Since only the basename of the mock configurations is used, this also works:
./package.sh fedora /etc/mock/fedora-21-x86_64.cfg /etc/mock/fedora-rawhide-i386.cfg
```

Debian and Ubuntu Linux
--------

To build and install Cura, run the following commands:

```bash
git clone https://github.com/daid/Cura.git

sudo apt-get install python-opengl python-numpy python-serial python-setuptools python-wxgtk2.8 curl

cd Cura

./package.sh debian_amd64          # or debian_i386 for 32bit
# this will prompt for your root password to run dpkg-deb

sudo dpkg -i ./scripts/linux/cura*.deb
```

Mac OS X
--------
The following section describes how to prepare working environment for developing and packaing for Mac OS X.
The working environment consist of build of Python, build of wxPython and all required Python packages.

We assume you already have Apple hardware with [64bit processor](http://support.apple.com/kb/HT3696) and you are familiar with tools like [virtualenv](http://pypi.python.org/pypi/virtualenv), [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) and [pip](http://www.pip-installer.org/en/latest/). Also ensure you have modern compiler installed.


###Install Python
You'll need **non-system**, **framework-based**, **universal** with **deployment target set to 10.6** build of Python 2.7

**non-system**: Output of
`python -c "import sys; print sys.prefix"`
should *not* start with *"/System/Library/Frameworks/Python.framework/"*.

**framework-based**: Output of
`python -c "import distutils.sysconfig as c; print(c.get_config_var('PYTHONFRAMEWORK'))"`
should be non-empty string. E.g. *Python*.

**universal**: Output of
``lipo -info `which python` ``
should include both i386 and x86_64. E.g *"Architectures in the fat file: /usr/local/bin/python are: i386 x86_64"*.

**deployment target set to 10.6**: Output of
``otool -l `which python` ``
should contain *"cmd LC_VERSION_MIN_MACOSX ... version 10.6"*.

The easiest way to install it is via [Homebrew](http://mxcl.github.com/homebrew/) using the formula from Cura's repo:
`brew install --build-bottle --fresh Cura/scripts/darwin/python.rb --universal`
Note if you already have Python installed via Homebrew, you have to uninstall it first.

You can also install [official build](http://www.python.org/ftp/python/2.7.3/python-2.7.3-macosx10.6.dmg).


FreeBSD
--------
On FreeBSD simply use the Port Tree (`cd /usr/ports/cad/cura`) to create (`make package`) and install (`make install`) the package as root. Port will check for all necessary dependencies. You can also use the provided binary package with `pkg install Cura`.

If you want to create an archive for local use the `package.sh freebsd` script (as an ordinary user) will give you a tarball with the program.


###Configure Virtualenv
Create new virtualenv. If you have [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) installed:
`mkvirtualenv Cura`

wxPython cannot be installed via pip, we have to build it from source by specifing prefix to our virtualenv.

Assuming you have virtualenv at *~/.virtualenvs/Cura/* and [wxPython sources](http://sourceforge.net/projects/wxpython/files/wxPython/2.9.4.0/wxPython-src-2.9.4.0.tar.bz2) at *~/Downloads/wxPython-src-2.9.4.0/*:

1. `cd` into *~/Downloads/wxPython-src-2.9.4.0/* and configure the sources:

        ./configure \
        CFLAGS='-msse2 -mno-sse3 -mno-sse4' \
        CXXFLAGS='-msse2 -mno-sse3 -mno-sse4' \
        --disable-debug \
        --enable-clipboard \
        --enable-display \
        --enable-dnd \
        --enable-monolithic \
        --enable-optimise \
        --enable-std_string \
        --enable-svg \
        --enable-unicode \
        --enable-universal_binary=i386,x86_64 \
        --enable-webkit \
        --prefix=$HOME/.virtualenvs/Cura/ \
        --with-expat \
        --with-libjpeg=builtin \
        --with-libpng=builtin \
        --with-libtiff=builtin \
        --with-macosx-version-min=10.6 \
        --with-opengl \
        --with-osx_cocoa \
        --with-zlib=builtin

2. `make install`
    Note to speedup the process I recommend you to enable multicore build by adding the -j*cores* flag:
    `make -j4 install`
3. `cd` into *~/Downloads/wxPython-src-2.9.4.0/wxPython/*
4. Build wxPython (Note `python` is the python of your virtualenv):

        python setup.py build_ext \
        BUILD_GIZMOS=1 \
        BUILD_GLCANVAS=1 \
        BUILD_STC=1 \
        INSTALL_MULTIVERSION=0 \
        UNICODE=1 \
        WX_CONFIG=$HOME/.virtualenvs/Cura/bin/wx-config \
        WXPORT=osx_cocoa

5. Install wxPython (Note `python` is the python of your virtualenv):

        python setup.py install \
        --prefix=$HOME/.virtualenvs/Cura \
        BUILD_GIZMOS=1 \
        BUILD_GLCANVAS=1 \
        BUILD_STC=1 \
        INSTALL_MULTIVERSION=0 \
        UNICODE=1 \
        WX_CONFIG=$HOME/.virtualenvs/Cura/bin/wx-config \
        WXPORT=osx_cocoa

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


###Package Cura into application
Ensure that virtualenv is activated, so `python` points to the python of your virtualenv (e.g. ~/.virtualenvs/Cura/bin/python).Use package.sh to build Cura:
`./package.sh darwin`

Note that application is only guaranteed to work on Mac OS X version used to build and higher, but may not support lower versions.
E.g. Cura built on 10.8 will work on 10.8 and 10.7, but not on 10.6. In other hand, Cura built on 10.6 will work on 10.6, 10.7 and 10.8.

