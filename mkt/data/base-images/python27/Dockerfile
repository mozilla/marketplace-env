FROM centos:centos6

ADD yum/mkt.repo  /etc/yum.repos.d/mkt.repo

RUN yum install -y python27

RUN yum install -y git
RUN yum install -y gcc

RUN yum install -y \
    python27-m2crypto \
    python27-python-lxml
RUN yum install -y libxslt

ENV PATH /opt/rh/python27/root/usr/bin:$PATH
ENV LD_LIBRARY_PATH /opt/rh/python27/root/usr/lib64
ENV LANG=en_US.UTF-8

RUN easy_install pip
RUN pip install ipython ipdb
