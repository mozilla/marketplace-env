FROM mozillamarketplace/centos-python27-mkt:0.5

RUN rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
RUN yum install -y erlang

RUN rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
RUN yum install -y http://www.rabbitmq.com/releases/rabbitmq-server/v2.8.4/rabbitmq-server-2.8.4-1.noarch.rpm

EXPOSE 5672 15672 25672 4369
ADD run.sh /
CMD /run.sh
