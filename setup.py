# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name='formsend',
    version='0.0.1',
    description='Send HTML forms to email.',
    author='Gennady Chibisov',
    author_email='web-chib@ya.ru',
    packages=find_packages('formsend'),
    package_dir={'': 'formsend'},
)