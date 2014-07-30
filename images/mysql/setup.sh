#!/bin/bash

# Install a MySQL DB
echo "=> Installing a new database"
mysql_install_db
chown -R mysql /var/lib/mysql/
chgrp -R mysql /var/lib/mysql/

# Start the MySQL server
echo "=> Starting mysql"
/usr/bin/mysqld_safe > /dev/null 2>&1 &

# Wait to confirm that it has started
RET=1
while [[ RET -ne 0 ]]; do
    sleep 1
    mysql -uroot -e "status" > /dev/null 2>&1
    RET=$?
done
echo "=> Mysql started"

# Create a root user with no password
echo "=> Created a root user with no password"
mysql -uroot -e "CREATE USER 'root'@'%' IDENTIFIED BY ''"
mysql -uroot -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION"

# Stop the server
echo "=> Stopping mysql"
mysqladmin -uroot shutdown
