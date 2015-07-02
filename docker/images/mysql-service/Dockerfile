FROM mozillamarketplace/centos-mysql-mkt:latest

RUN mv /etc/my.cnf{,.bck}
ADD my.cnf /etc/my.cnf
ADD setup.sh /setup.sh
ADD run.sh /run.sh

EXPOSE 3306

CMD ["/bin/bash", "/run.sh"]
