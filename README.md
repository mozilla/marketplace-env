# Wharfie

A project to bring together a turn-key marketplace development environment using Docker containers.

*Note: This is currently in active development and should be considered experimental.*

## Setup

To get set-up we'd suggest creating a virtualenv after installing virtualenvwrapper

### Install virtualenvwrapper

    pip install virtualenvwrapper

### Create the virtualenv

    $ mkvirtualenv wharfie
    $ workon wharfie
    $ pip install -r requirements.txt


## Pimping boot2docker with virtualbox additions

    $ mv ~/.boot2docker/boot2docker.iso{,.bck}
    $ curl -o ~/.boot2docker/boot2docker.iso https://dl.dropboxusercontent.com/u/8877748/boot2docker.iso

### Updating the custom boot2docker.iso

    $ bin/build-b2d-dockerfile.sh
    $ bin/wharfie build boot2docker

Next create the iso by running:

    $ docker run -i -t --rm boot2docker_img /bin/bash

Then in a second shell (Get the container id with docker ps):

    $ docker cp <Container-ID>:boot2docker.iso $TMPPATH/boot2docker.iso
