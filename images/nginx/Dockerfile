FROM mozillamarketplace/centos-python27-mkt:0.5

RUN yum install -y nginx

ADD nginx.conf /etc/nginx/conf.d/marketplace.conf

EXPOSE 80

CMD ['nginx', '-c', '/etc/nginx/nginx.conf', '-g', '"daemon off;"']
