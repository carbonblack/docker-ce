Name: docker-ce
Version: %{_version}
Release: %{_release}%{?dist}
Summary: The open-source application container engine
Group: Tools/Docker
License: ASL 2.0
Source0: engine.tgz
Source1: cli.tgz
URL: https://www.docker.com
Vendor: Docker
Packager: Docker <support@docker.com>

# DWZ problem with multiple golang binary, see bug
# https://bugzilla.redhat.com/show_bug.cgi?id=995136#c12
%global _dwz_low_mem_die_limit 0
%global is_systemd 0
%global with_selinux 0

Requires(post): chkconfig
Requires(preun): chkconfig
# This is for /sbin/service
Requires(preun): initscripts

# required packages on install
Requires: /bin/sh
Requires: iptables
Requires: libcgroup
Requires: tar
Requires: xz

# Resolves: rhbz#1165615
Requires: device-mapper-libs >= 1.02.90-1

# conflicting packages
Conflicts: docker
Conflicts: docker-io
Conflicts: docker-engine-cs
Conflicts: docker-ee

# Obsolete packages
Obsoletes: docker-ce-selinux
Obsoletes: docker-engine-selinux
Obsoletes: docker-engine

%description
Docker is an open source project to build, ship and run any application as a
lightweight container.

Docker containers are both hardware-agnostic and platform-agnostic. This means
they can run anywhere, from your laptop to the largest EC2 compute instance and
everything in between - and they don't require you to use a particular
language, framework or packaging system. That makes them great building blocks
for deploying and scaling web apps, databases, and backend services without
depending on a particular stack or provider.

%prep
%setup -q -c -n src -a 1

%build
export DOCKER_GITCOMMIT=%{_gitcommit}
mkdir -p /go/src/github.com/docker
rm -f /go/src/github.com/docker/cli
ln -s /root/rpmbuild/BUILD/src/cli /go/src/github.com/docker/cli
pushd /go/src/github.com/docker/cli
make VERSION=%{_origversion} GITCOMMIT=%{_gitcommit} dynbinary manpages # cli
popd
pushd engine
TMP_GOPATH="/go" hack/dockerfile/install-binaries.sh runc-dynamic containerd-dynamic proxy-dynamic tini
hack/make.sh dynbinary
popd

%check
cli/build/docker -v
engine/bundles/%{_origversion}/dynbinary-daemon/dockerd -v

%install
# install binary
install -d $RPM_BUILD_ROOT/%{_bindir}
install -p -m 755 cli/build/docker $RPM_BUILD_ROOT/%{_bindir}/docker
install -p -m 755 engine/bundles/%{_origversion}/dynbinary-daemon/dockerd-%{_origversion} $RPM_BUILD_ROOT/%{_bindir}/dockerd

# install proxy
install -p -m 755 /usr/local/bin/docker-proxy $RPM_BUILD_ROOT/%{_bindir}/docker-proxy

# install containerd
install -p -m 755 /usr/local/bin/docker-containerd $RPM_BUILD_ROOT/%{_bindir}/docker-containerd
install -p -m 755 /usr/local/bin/docker-containerd-shim $RPM_BUILD_ROOT/%{_bindir}/docker-containerd-shim
install -p -m 755 /usr/local/bin/docker-containerd-ctr $RPM_BUILD_ROOT/%{_bindir}/docker-containerd-ctr

# install runc
install -p -m 755 /usr/local/bin/docker-runc $RPM_BUILD_ROOT/%{_bindir}/docker-runc

# install tini
install -p -m 755 /usr/local/bin/docker-init $RPM_BUILD_ROOT/%{_bindir}/docker-init

# install udev rules
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/udev/rules.d
install -p -m 644 engine/contrib/udev/80-docker.rules $RPM_BUILD_ROOT/%{_sysconfdir}/udev/rules.d/80-docker.rules

# add init scripts
install -d $RPM_BUILD_ROOT/etc/sysconfig
install -d $RPM_BUILD_ROOT/%{_initddir}
install -p -m 644 engine/contrib/init/sysvinit-redhat/docker.sysconfig $RPM_BUILD_ROOT/etc/sysconfig/docker
install -p -m 755 engine/contrib/init/sysvinit-redhat/docker $RPM_BUILD_ROOT/%{_initddir}/docker
# add bash, zsh, and fish completions
install -d $RPM_BUILD_ROOT/usr/share/bash-completion/completions
install -d $RPM_BUILD_ROOT/usr/share/zsh/vendor-completions
install -d $RPM_BUILD_ROOT/usr/share/fish/vendor_completions.d
install -p -m 644 engine/contrib/completion/bash/docker $RPM_BUILD_ROOT/usr/share/bash-completion/completions/docker
install -p -m 644 engine/contrib/completion/zsh/_docker $RPM_BUILD_ROOT/usr/share/zsh/vendor-completions/_docker
install -p -m 644 engine/contrib/completion/fish/docker.fish $RPM_BUILD_ROOT/usr/share/fish/vendor_completions.d/docker.fish

# install manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 cli/man/man1/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1
install -d %{buildroot}%{_mandir}/man5
install -p -m 644 cli/man/man5/*.5 $RPM_BUILD_ROOT/%{_mandir}/man5
install -d %{buildroot}%{_mandir}/man8
install -p -m 644 cli/man/man8/*.8 $RPM_BUILD_ROOT/%{_mandir}/man8

# add vimfiles
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/doc
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/ftdetect
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/syntax
install -p -m 644 engine/contrib/syntax/vim/doc/dockerfile.txt $RPM_BUILD_ROOT/usr/share/vim/vimfiles/doc/dockerfile.txt
install -p -m 644 engine/contrib/syntax/vim/ftdetect/dockerfile.vim $RPM_BUILD_ROOT/usr/share/vim/vimfiles/ftdetect/dockerfile.vim
install -p -m 644 engine/contrib/syntax/vim/syntax/dockerfile.vim $RPM_BUILD_ROOT/usr/share/vim/vimfiles/syntax/dockerfile.vim

# add nano
install -d $RPM_BUILD_ROOT/usr/share/nano
install -p -m 644 engine/contrib/syntax/nano/Dockerfile.nanorc $RPM_BUILD_ROOT/usr/share/nano/Dockerfile.nanorc

mkdir -p build-docs
for engine_file in AUTHORS CHANGELOG.md CONTRIBUTING.md LICENSE MAINTAINERS NOTICE README.md; do
    cp "engine/$engine_file" "build-docs/engine-$engine_file"
done
for cli_file in LICENSE MAINTAINERS NOTICE README.md; do
    cp "cli/$cli_file" "build-docs/cli-$cli_file"
done

# list files owned by the package here
%files
%doc build-docs/engine-AUTHORS build-docs/engine-CHANGELOG.md build-docs/engine-CONTRIBUTING.md build-docs/engine-LICENSE build-docs/engine-MAINTAINERS build-docs/engine-NOTICE build-docs/engine-README.md
%doc build-docs/cli-LICENSE build-docs/cli-MAINTAINERS build-docs/cli-NOTICE build-docs/cli-README.md
/%{_bindir}/docker
/%{_bindir}/dockerd
/%{_bindir}/docker-containerd
/%{_bindir}/docker-containerd-shim
/%{_bindir}/docker-containerd-ctr
/%{_bindir}/docker-proxy
/%{_bindir}/docker-runc
/%{_bindir}/docker-init
/%{_sysconfdir}/udev/rules.d/80-docker.rules
%config(noreplace,missingok) /etc/sysconfig/docker
/%{_initddir}/docker
/usr/share/bash-completion/completions/docker
/usr/share/zsh/vendor-completions/_docker
/usr/share/fish/vendor_completions.d/docker.fish
%doc
/%{_mandir}/man1/*
/%{_mandir}/man5/*
/%{_mandir}/man8/*
/usr/share/vim/vimfiles/doc/dockerfile.txt
/usr/share/vim/vimfiles/ftdetect/dockerfile.vim
/usr/share/vim/vimfiles/syntax/dockerfile.vim
/usr/share/nano/Dockerfile.nanorc

%post
# This adds the proper /etc/rc*.d links for the script
/sbin/chkconfig --add docker
if ! getent group docker > /dev/null; then
    groupadd --system docker
fi

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service docker stop >/dev/null 2>&1
    /sbin/chkconfig --del docker
fi

%postun
if [ "$1" -ge "1" ] ; then
    /sbin/service docker condrestart >/dev/null 2>&1 || :
fi

%changelog

* Tue Aug 08 2017 <tlusk@carbonblack.com> 17.06.0-ce
- Add CentOS 6 support
