#!/usr/bin/env python

from setuptools import setup

install_requires = [
    "aiohttp>=3.5.4,<4",
    "opencv-python>=4.1.0.25,<5",
    "nltk>=3.4.3,<4",
    "Pillow>=6.0.0,<7",
    "numpy>=1.16.4,<2",
]

tests_require = []

python_requires = '>=3'

setup(
    name='newsapy',
    packages=["newsapy"],
    version='0.2.10',
    license='MIT',
    url='https://everyonegetinhere.com',
    install_requires=install_requires,
    description='An unofficial asynchronous, key-switching Python client for NewsAPI',
    download_url='https://github.com/CocoPommel/newsapy/archive/0.2.10.tar.gz',
    keywords=['newsapy', 'newsapi', 'news'],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Information Technology',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
