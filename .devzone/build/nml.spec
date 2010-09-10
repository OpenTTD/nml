# define macro for older distros
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           %{dz_repo}
Version:        %{dz_version}
Release:        %{_vendor}%{?suse_version}
Summary:        NewGRF Meta Language
Group:          Development/Tools
License:        GPLv2
URL:            http://dev.openttdcoop.org/projects/nml
Source0:        nml-%{version}.tar
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
#We need for regression test the required packages also on building:
BuildRequires:  python-ply python-imaging
#We need Mercurial for auto version detection:
BuildRequires:  mercurial

%description
A tool to compile nml files to grf or nfo files,, making newgrf coding easier.

%prep
%setup -qn %{name}
%{__python} setup.py sdist
#Add ".src" to the source archive file name:
rename .tar.gz .src.tar.gz dist/*

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT --prefix=%{_prefix} --record=INSTALLED_FILES

%check
cd regression
make 1>%{name}-%{version}-build.test.log 2>&1

%files -f INSTALLED_FILES 
%defattr(-,root,root,-)
%dir %{python_sitelib}/nml
%dir %{python_sitelib}/nml/actions

%changelog
