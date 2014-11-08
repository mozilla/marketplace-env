from glob import glob
from setuptools import setup


images = ['images/README.md']
images += glob('images/*/*')

base_images = ['base-images/README.md']
base_images += glob('base-images/*/Dockerfile')
base_images += glob('base-images/mysql/yum/*')

setup(
    name='marketplace-docker',
    version='0.1',
    description='Docker tools for the marketplace',
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
            'mkt = mkt.cmds:main'
        ]
    },
    data_files=[
        ('mkt-data', ['fig.yml.dist']),
        ('mkt-data/images', images),
        ('mkt-data/base-images', base_images),
    ],
    requires=[
        'fig',
    ],
    zip_safe=False
)
