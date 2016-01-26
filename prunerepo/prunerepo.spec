Summary: Remove old packages from rpm-md repository
Name: prunerepo
Version: 1.2
Release: 1%{?dist}

# Source is created by:
# git clone https://git.fedorahosted.org/git/copr.git
# cd copr/prunerepo
# tito build --tgz
Source0: %{name}-%{version}.tar.gz

License: GPLv2+
BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: rpm-python3
BuildRequires: asciidoc
Requires: createrepo_c
Requires: dnf-plugins-core
Requires: rpm-python3
Requires: python3

%description
Removes obsoleted package versions from a yum repository. Both
rpms and srpms, that have a newer version available in that same
repository, are deleted from filesystem and rpm-md metadata are 
recreated afterwards. Support for specific repository structure
(e.g. COPR) is also available making it possible to additionally
remove build logs and whole build directories associated with a 
package. After deletion of obsoleted packages, the command
"createrepo_c --database --update" is called to recreate the
repository metadata.

%prep
%setup -q

%build
%py3_build
a2x -d manpage -f manpage man/prunerepo.1.asciidoc

%install
%py3_install

install -d %{buildroot}%{_mandir}/man1
install -p -m 644 man/prunerepo.1 %{buildroot}/%{_mandir}/man1/

%files
%license LICENSE

%{python3_sitelib}/*
%{_bindir}/prunerepo
%{_mandir}/man1/prunerepo.1*

%changelog
* Tue Jan 26 2016 clime <clime@redhat.com> 1.2-1
- bugfix for --cleancopr when a log for the respective dir does not
  exist (e.g. copr repos with old dir naming)

* Mon Jan 25 2016 clime <clime@redhat.com> 1.1-1
- test suite finished (clime@redhat.com)
- --quiet, --cleancopr and --days options implemented (clime@redhat.com)
* Tue Jan 19 2016 clime <clime@redhat.com> 1.0-1
- Initial package version
