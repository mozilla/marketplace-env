from glob import glob
from setuptools import setup


images = glob('mkt-data/images/*/*')

base_images = glob('mkt-data/base-images/*/Dockerfile')
base_images += glob('mkt-data/base-images/mysql/yum/*')

setup(
    name='marketplace-env',
    version='0.1.1',
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
    data_files=[
        ('mkt-data/images', images),
        ('mkt-data/base-images', base_images),
        ('mkt-data', ['mkt-data/fig.yml.dist']),
    ],
    requires=[
        'fig',
        'netifaces'
    ],
    zip_safe=False
)

