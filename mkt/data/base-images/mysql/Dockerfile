FROM mozillamarketplace/centos-python27-mkt:0.6

ADD yum/mysql.repo /etc/yum.repos.d/mysql.repo
RUN yum install -y mysql-community-server mysql-community-devel && yum clean all
