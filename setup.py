#!/usr/bin/env python3

import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# print(read('requirements.txt').split('\n'))
# the setup
setup(
    name='allamericanregress',
    version=0.1,
    description='Capstone project.',
    # long_description=read('README'),
    url='https://github.com/jcrayz/Capstone',
    author='AllAmericanRegress',
    author_email='',
    include_package_data=True,
    setup_requires=[],
)
