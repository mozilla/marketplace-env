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

### Clone needed repos

Clone following repos into `trees/`:

 * https://github.com/mozilla/fireplace
 * https://github.com/mozilla/spartacus
 * https://github.com/mozilla/solitude
 * https://github.com/mozilla/webpay

### fig

Install [fig](http://www.fig.sh/) and run following command:

    $ fig up

## Updating boot2docker with virtualbox additions to support volume mounts (OSX hosts)

You'll need boot2docker installed on OSX. This provides a lightweight VM + an osx docker binary.
The Docker command talks to the vm and the vm manages the docker containers.

You'll also need virtualbox installed. Once boot2docker is setup run the following commands.

    $ boot2docker stop

    $ mv ~/.boot2docker/boot2docker.iso{,.bck}
    $ curl -o ~/.boot2docker/boot2docker.iso https://dl.dropboxusercontent.com/u/8877748/boot2docker.iso

    $ VBoxManage sharedfolder add boot2docker-vm -name trees -hostpath '<PATH_TO_WHARFIE>/wharfie/trees/'
    $ boot2docker up
    $ boot2docker ssh "sudo modprobe vboxsf && sudo mkdir -p '<PATH_TO_WHARFIE>/wharfie/trees/'  && sudo mount -t vboxsf trees <PATH_TO_WHARFIE>/wharfie/trees/"

### Updating the custom boot2docker.iso

Note: This is something that most users should never need to do.

    $ bin/build-b2d-dockerfile.sh
    $ bin/wharfie build boot2docker

Next create the iso by running:

    $ docker run -i -t --rm boot2docker_img /bin/bash

Then in a second shell (Get the container id with docker ps):

    $ docker cp <Container-ID>:boot2docker.iso <TMPPATH>/boot2docker.iso
