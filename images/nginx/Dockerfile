FROM    centos:centos6

ADD yum/mkt.repo  /etc/yum.repos.d/mkt.repo

RUN yum install -y nginx

ADD nginx.conf /etc/nginx/conf.d/marketplace.conf

EXPOSE 80

CMD ['nginx', '-c', '/etc/nginx.conf', '-g', 'daemon off;']
