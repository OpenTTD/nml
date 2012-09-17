# define macro for older distros
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           %{dz_repo}
Version:        %{dz_version}
Release:        %{_vendor}%{?suse_version}
Summary:        NewGRF Meta Language
Group:          Development/Tools
License:        GPLv2
URL:            http://dev.openttdcoop.org/projects/nml
Source0:        %{name}-%{version}.tar
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
%if %{?suse_version: %{suse_version} > 1110} %{!?suse_version:1}
BuildArch:      noarch
%endif
%if 0%{?suse_version} > 1100
BuildRequires:  python-base
%else
BuildRequires:  python-devel
%endif
Provides:       nmlc
Requires:       python-ply python-imaging
# We need for regression test the required packages also on building:
BuildRequires:  python-ply python-imaging
# We need Mercurial for auto version detection:
BuildRequires:  mercurial
# We need wine for windows nmlc.exe
BuildRequires:  nml-dot-wine p7zip
# We use setuptools for the packaging
BuildRequires:  python-setuptools

%description
A tool to compile nml files to grf or nfo files, making newgrf coding easier.

%prep
%setup -qn %{name}

# update to the tag, if not revision
[ "$(echo %{version} | cut -b-1)" != "r" ] && hg up %{version}

# prepare wine:
install-nml-dot-wine

%build
%{__python} setup.py build

# create windows executable
#python -c "import nml.version_info; nml.version_info.get_and_write_version()"
wine "C:\\Python27\\pythonw.exe" "C:\\Python27\\Scripts\\cxfreeze" nmlc
cp $HOME/.wine/drive_c/windows/system32/python27.dll dist/
mv dist nmlc-exe && mkdir dist
cd nmlc-exe
7za a -l -tzip -mx=9 ../dist/%{name}-%{version}-windows-win32.zip *
cd ..

# build source bundle:
%{__python} setup.py sdist
# Add ".src" to the source archive file name:
rename .tar.gz .src.tar.gz dist/*

%install
%{__python} setup.py install --skip-build --root=%{buildroot} --prefix=%{_prefix}
install -D -m0644 docs/nmlc.1 %{buildroot}%{_mandir}/man1/nmlc.1
#setuptools should not be a requirement on running, so we install the nmlc wrapper from source
install -m0755 nmlc %{buildroot}%{_bindir}/nmlc

%check
cd regression
PYTHONPATH=%{buildroot}%{python_sitelib} make _V= NMLC=%{buildroot}%{_bindir}/nmlc 1>%{name}-%{version}-build.test.log 2>&1

%files
%defattr(-,root,root,-)
%doc docs/*.txt
%{_bindir}/nmlc
%{_mandir}/man1/nmlc.1*
%{python_sitelib}/*

%changelog
