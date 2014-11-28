import os
from setuptools import setup


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


setup(
    name='marketplace-env',
    version='0.1.5',
    description='Tools for building the Firefox Marketplace using Docker.',
    author='Marketplace Developers',
    author_email='marketplace-devs@mozilla.com',
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
        'fig',
        'netifaces'
    ],
    zip_safe=False
)

