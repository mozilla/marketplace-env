import os
import re
from setuptools import setup
from setuptools.command.install import install


def get_version(package):
    """
    Return package version as listed in `__version__` in `version.py`.
    """
    init_py = open(os.path.join(package, 'version.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves. Copied from django_rest_framework.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]
    filepaths = []

    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                         for filename in filenames])
    return {package: filepaths}


class Custom(install):

    def run(self):
        """
        Override the run command, so that post setup we can run our
        own commands, to keep the docker-compose yml up to date with any
        changes from the library.
        """
        install.run(self)

        from mkt.cmds import get_config_value, update_config # flake8: noqa

        # If there is not a config value, then it's never been run. Don't
        # guess, we'll just abort instead.
        if not get_config_value('paths', 'root', None):
            return

        # There is a value, rewrite the config so it's got the latest goodness
        # in it.
        update_config(None, None)


setup(
    name='marketplace-env',
    version=get_version('mkt'),
    description='Tools for building the Firefox Marketplace using Docker.',
    author='Marketplace Developers',
    author_email='marketplace-devs@mozilla.com',
    cmdclass={
        'install': Custom
    },
    license='MPL2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
    ],
    packages=[
        'mkt',
    ],
    entry_points={
        'console_scripts': [
            'mkt = mkt.bin:main'
        ]
    },
    package_data=get_package_data('mkt'),
    install_requires=[
        'argcomplete',
        'docker-compose',
        'netifaces'
    ],
    zip_safe=False
)
