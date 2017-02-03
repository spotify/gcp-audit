#!/usr/bin/env python

# Copyright (c) 2016-2017 Spotify AB.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from codecs import open
from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gcp-audit',
    version='1.0.0',
    description='A tool for auditing security properties of GCP projects.',
    long_description=long_description,
    url='https://github.com/spotify/gcp-audit',
    author='Spotify Security',
    author_email='security@spotify.com',
    license='License :: OSI Approved :: Apache Software License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Security',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='security gcp google-cloud-platform',
    packages=find_packages(),
    install_requires=['termcolor', 'google-api-python-client', 'PyYAML'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'gcp-audit=gcp_audit.gcp_audit:main'
        ],
    },
)
