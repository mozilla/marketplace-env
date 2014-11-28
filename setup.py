import os
from glob import glob
from setuptools import setup

files = ['mkt-data/fig.yml.dist']
files += glob('mkt-data/images/*/*')
files += glob('mkt-data/base-images/*/Dockerfile')
files += glob('mkt-data/base-images/mysql/yum/*')

files = [(os.path.dirname(f), (f,)) for f in files]

setup(
    name='marketplace-env',
    version='0.1.4',
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
    data_files=files,
    install_requires=[
        'fig',
        'netifaces'
    ],
    zip_safe=False
)

