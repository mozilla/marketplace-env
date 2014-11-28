[![Build Status](https://travis-ci.org/mozilla/marketplace-env.svg?branch=master)](https://travis-ci.org/mozilla/marketplace-env)

Automates the setup of a Marketplace development environment, prominently for
the backend, using Docker containers.

* [Docker instructions](https://marketplace.readthedocs.org/en/latest/topics/backend.html)
* [Marketplace documentation](https://marketplace.readthedocs.org)

## Changes

### 0.1.2

- fix images and base images paths in setup

### 0.1.1

- fix fig.yml.dist paths in setup by moving to mkt-data

### 0.1

- Move to a library installable by pip.
- Add in generating fig.yml through a template.
- Add in commands root and up.

### Upgrading to 0.1

We'd recommend not using a checked out version of marketplace-env anymore
and switch over to pip installing mkt. If you do this be sure to preserve the
checkouts you've got.

The new version allows you to explicitly specify a directory for where project
checkouts should live, whereas the old version checked it all out into "trees".

However, if you've previously got marketplace-env (or wharfie) checked out then
you should be able to update and run the following commands:

  bin/mkt root trees

And then add the two environment variables:

  export FIG_FILE=~/.mkt.fig.yml
  export FIG_PROJECT_NAME=mkt

You'll then need to a:

  fig build

After that you should be good to go.
