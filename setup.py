#!/usr/bin/env python

from setuptools import setup, find_packages

install_requires = [
    "aiohttp==3.5.4",
    "opencv-python==4.1.0.25",
    "nltk==3.4.3",
    "Pillow>=6.0.0",
    "numpy>=1.16.4",
]

tests_require = []

python_requires = '>=3'

setup(
    name='newsapy',
    version='0.1.2',
    license='MIT',
    url='https://everyonegetinhere.com',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    description='An unofficial asynchronous, key-switching Python client for NewsAPI',
    download_url='https://github.com/mattlisiv/newsapi-python/archive/master.zip',
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
