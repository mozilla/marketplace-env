[![Build Status](https://travis-ci.org/mozilla/marketplace-env.svg?branch=master)](https://travis-ci.org/mozilla/marketplace-env)
[![PyPI version](https://badge.fury.io/py/marketplace-env.svg)](http://badge.fury.io/py/marketplace-env)

Automates the setup of a Marketplace development environment, prominently for
the backend, using Docker containers.

* [Docker instructions](https://marketplace.readthedocs.org/en/latest/topics/backend.html)
* [Marketplace documentation](https://marketplace.readthedocs.org)

## Changes

### 0.1.8

- Allow `mkt bash` into images as well as projects, eg: nginx
- run zamboni, webpay and solitude through supervisord (bug 1122190)
- run receipt verifier for zamboni (bug 1109334)
- default master to moz in the checkout

### 0.1.3-5

- Various fixes to packaging just because.

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

```shell
  bin/mkt root trees
```

And then add the two environment variables:

```shell
  export FIG_FILE=~/.mkt.fig.yml
  export FIG_PROJECT_NAME=mkt
```

You'll then need to run:

```shell
  fig build
```

After that you should be good to go.
