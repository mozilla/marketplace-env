
FROM mozillamarketplace/centos-python27-mkt:0.5

RUN yum install -y elasticsearch-plugin-analysis-icu \
    elasticsearch \
    java-1.7.0-openjdk \
    which

RUN mkdir -p /usr/local/var/log/
RUN chown -R elasticsearch /usr/local/var/log/

RUN curl -o /etc/elasticsearch/elasticsearch.yml https://raw.githubusercontent.com/mozilla/zamboni/master/scripts/elasticsearch/elasticsearch.yml

EXPOSE 9200
