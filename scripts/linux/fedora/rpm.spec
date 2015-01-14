%global _curaName      __curaName__
%global _baseDir       __basedir__
%global _version       __version__
%global _gitCura       __gitCura__
%global _gitCuraEngine __gitCuraEngine__
%global _gitPower      __gitPower__


Name:             %{_curaName}
Version:          %{_version}
Release:          1%{?dist}
Summary:          3D printing software aimed at RepRaps and the Ultimaker
Group:            Applications/Engineering

License:          GPLv2+
URL:              https://github.com/daid/Cura.git
Source0:          %{_curaName}-%{_version}.tar.gz

BuildRequires:    libstdc++-static, glibc-static
Requires:         wxPython, curl
Requires:         python3-setuptools >= 0.6.34
Requires:         python3-PyOpenGL >= 3.0.2, PyOpenGL >= 3.0.2
Requires:         python3-pyserial >= 2.6, pyserial >= 2.6
Requires:         python3-numpy >= 1.6.2, numpy >= 1.6.2
Requires:         python3-power >= 1.2


%description
%{_curaName} is a full software solution for 3D printing, aimed at RepRaps and
the Ultimaker.

It's free software payed for and maintained by Ultimaker.


%prep
%setup -q -n %{name}-%{version}


%build
make -C CuraEngine VERSION=%{_version}

dstDir="%{_baseDir}/usr/share/cura"

rm    -frv "$dstDir"
mkdir -pv  "$dstDir"

cp -av -t  "$dstDir" \
  Cura \
  resources \
  plugins \
  CuraEngine/build/CuraEngine \
  Power/power \
  scripts/linux/cura.py

echo "%{_version}" > "$dstDir/Cura/version"
cat > "$dstDir/Cura/versions" << EOF
# Git SHAs of software used to build %{_curaName}
Cura       : %{_gitCura}
CuraEngine : %{_gitCuraEngine}
Power      : %{_gitPower}
EOF


%install
mkdir -pv "%{buildroot}"
cp -av -t "%{buildroot}" "%{_baseDir}/usr"


%files
%defattr(-,root,root)
%{_bindir}/cura
%attr(644, root, root) %{_datarootdir}/applications/cura.desktop
%attr(755, root, root) %{_datarootdir}/cura/Cura/cura.py
%attr(755, root, root) %{_datarootdir}/cura/Cura/util/pymclevel/mce.py
%attr(755, root, root) %{_datarootdir}/cura/CuraEngine
%attr(755, root, root) %{_datarootdir}/cura/cura.py
%{_datarootdir}/cura


%changelog
* Wed Jan 14 2015 Ferry Huberts <ferry.huberts@pelagic.nl>
- Initial packaging, currently at version 15.01.RC7
