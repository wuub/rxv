#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, division, print_function

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


setup(
    name='rxv',
    version='0.2.0',
    description='Automation Library for Yamaha RX-V473, RX-V573, RX-V673, RX-V773 receivers',
    long_description=open('README.rst').read(),
    author='Wojciech Bederski',
    url="https://github.com/wuub/rxv",
    license='MIT',
    author_email='github@wuub.net',
    packages=find_packages(),
    install_requires=['requests'],
    tests_require=['tox'],
    zip_safe=False,
    cmdclass={'test': Tox},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Home Automation",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: PyPy"
    ]
)
