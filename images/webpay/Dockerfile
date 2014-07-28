FROM   muffinresearch/centos-python27-mkt:latest

RUN yum install -y git
RUN yum install -y gcc
RUN yum install -y \
    python27-m2crypto \
    python27-python-lxml

ADD . /src
RUN mkdir -p /pip/cache
RUN pip install --download-cache /pip/cache --no-deps -r /src/requirements/docker.txt

EXPOSE  2601

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:2601"]
