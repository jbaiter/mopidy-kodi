from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-Kodi',
    version=get_version('mopidy_kodi/__init__.py'),
    url='https://github.com/jbaiter/mopidy-kodi',
    license='Apache License, Version 2.0',
    author='Johannes Baiter',
    author_email='johannes.baiter@gmail.com',
    description='Mopidy extension for playing music from your Kodi library',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
        'cachetools >= 1.1.6',
        'jsonrpc-requests >= 0.1',
    ],
    entry_points={
        'mopidy.ext': [
            'kodi = mopidy_kodi:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
