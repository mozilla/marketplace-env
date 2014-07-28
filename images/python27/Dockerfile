FROM    centos:centos6

ADD yum/mkt.repo  /etc/yum.repos.d/mkt.repo

RUN yum install -y python27

env PATH /opt/rh/python27/root/usr/bin:$PATH
env LD_LIBRARY_PATH /opt/rh/python27/root/usr/lib64

RUN easy_install pip
