FROM mysql 

RUN yum install -y python-devel
RUN yum install -y git
RUN yum install -y gcc
RUN yum install -y \
    python27-m2crypto \
    python27-python-lxml

ADD solitude /src 
RUN mkdir -p /pip/cache
RUN pip install --download-cache /pip/cache --no-deps -r /src/requirements/dev.txt

EXPOSE  2602

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:2602"]
