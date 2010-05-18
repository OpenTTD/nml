# define macro for older distros
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           %{dz_repo}
Version:        %{dz_version}
Release:        %{_vendor}%{?suse_version}
Summary:        NFO Meta Language
Group:          Development/Tools
License:        GPLv2
URL:            http://dev.openttdcoop.org/projects/nml
# hg archive -ttbz2 nml-r`hg id -n`.tar.bz2
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
Provides:       nml2nfo
Requires:       python-ply python-imaging

%description
A tool to convert a meta-language to nfo, making newgrf coding easier.

%prep
%setup -qn %{name}
%{__python} setup.py sdist
mv dist/nml-`%{__python} setup.py -V`.tar.gz dist/nml-%{version}.src.tar.gz

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT --prefix=%{_prefix} --record=INSTALLED_FILES

%clean

%files -f INSTALLED_FILES 
%defattr(-,root,root,-)
%dir %{python_sitelib}/nml
%dir %{python_sitelib}/nml/actions

%changelog

