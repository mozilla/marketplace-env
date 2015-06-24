[![Build Status](https://travis-ci.org/mozilla/marketplace-env.svg?branch=master)](https://travis-ci.org/mozilla/marketplace-env)
[![PyPI version](https://badge.fury.io/py/marketplace-env.svg)](http://badge.fury.io/py/marketplace-env)

Automates the setup of a Marketplace development environment, prominently for
the backend, using Docker containers.

* [Docker instructions](https://marketplace.readthedocs.org/en/latest/topics/backend.html)
* [Marketplace documentation](https://marketplace.readthedocs.org)

## Changelog 

See https://github.com/mozilla/marketplace-env/releases

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
  export COMPOSE_FILE=~/.mkt.fig.yml
  export COMPOSE_PROJECT_NAME=mkt
```

You'll then need to run:

```shell
  docker-compose build
```

After that you should be good to go.
