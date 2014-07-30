FROM muffinresearch/centos-python27-mkt:latest 

ADD yum/mysql.repo /etc/yum.repos.d/mysql.repo
RUN yum install -y mysql-community-server

ADD my.cnf /etc/mysql/conf.d/my.cnf
ADD setup.sh /setup.sh
ADD run.sh /run.sh

EXPOSE 3306

CMD ["/bin/bash", "/run.sh"]
