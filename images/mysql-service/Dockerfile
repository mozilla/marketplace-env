FROM mozillamarketplace/centos-mysql-mkt:0.1

ADD my.cnf /etc/mysql/conf.d/my.cnf
ADD setup.sh /setup.sh
ADD run.sh /run.sh

EXPOSE 3306

CMD ["/bin/bash", "/run.sh"]
