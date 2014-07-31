FROM muffinresearch/centos-python27-mkt:0.4

RUN yum install -y nginx

ADD nginx.conf /etc/nginx/conf.d/marketplace.conf

EXPOSE 80

CMD ['/usr/sbin/nginx', '-c', '/etc/nginx/nginx.conf', '-g', '"daemon off;"']
