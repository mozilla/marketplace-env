FROM centos:centos6

ADD yum/mysql.repo /etc/yum.repos.d/mysql.repo
RUN yum install -y mysql-community-server mysql-community-devel; yum -y clean all
