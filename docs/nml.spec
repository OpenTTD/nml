#
# spec file for package nml
#
# Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           nml
Version:        0.3.1
Release:        0
Summary:        NewGRF Meta Language
License:        GPL-2.0+
Group:          Development/Tools/Building
Url:            http://dev.openttdcoop.org/projects/nml
Source0:        http://bundles.openttdcoop.org/nml/releases/%{version}/%{name}-%{version}.src.tar.gz
BuildRequires:  python-devel >= 2.6
BuildRequires:  python-setuptools
#We need for regression test the required packages also on building:
BuildRequires:  python-imaging
BuildRequires:  python-ply
Requires:       python-imaging
Requires:       python-ply
Provides:       nmlc = %{version}
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%if 0%{?suse_version} && 0%{?suse_version} <= 1110
%{!?python_sitelib: %global python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%else
BuildArch:      noarch
%endif

%description
A tool to compile nml files to grf or nfo files, making newgrf coding easier.

%prep
%setup -q

%build
python setup.py build

%install
python setup.py install --skip-build --root=%{buildroot} --prefix=%{_prefix}
install -D -m0644 docs/nmlc.1 %{buildroot}%{_mandir}/man1/nmlc.1
#setuptools should not be a requirement on running, so we install the nmlc wrapper from source
install -m0755 nmlc %{buildroot}%{_bindir}/nmlc

%check
cd regression
PYTHONPATH=%{buildroot}%{python_sitelib} make _V= NMLC=%{buildroot}%{_bindir}/nmlc

%files
%defattr(-,root,root,-)
%doc docs/*.txt
%{_bindir}/nmlc
%{_mandir}/man1/nmlc.1*
%{python_sitelib}/*

%changelog
