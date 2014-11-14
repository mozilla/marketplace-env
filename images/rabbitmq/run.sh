#!/usr/bin/env bash

if [ ! -d "/var/lib/rabbitmq/mnesia" ]; then
    /usr/sbin/rabbitmq-server & /usr/sbin/rabbitmqctl wait /var/lib/rabbitmq/mnesia/rabbit*.pid
    rabbitmqctl add_user zamboni zamboni
    rabbitmqctl set_user_tags zamboni administrator
    rabbitmqctl add_vhost zamboni
    rabbitmqctl set_permissions zamboni ".*" ".*" ".*"
    rabbitmqctl set_permissions -p zamboni zamboni ".*" ".*" ".*"
    rabbitmqctl stop /var/lib/rabbitmq/mnesia/rabbit*.pid
fi

/usr/sbin/rabbitmq-server
