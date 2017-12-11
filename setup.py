import sys
import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

longdesc = '''
This is a library for basic distributed networking, with varying
applications from microservice-like architectures to robotics
middleware.
'''

# Version info -- read without importing
_locals = {}
with open('autocore/_version.py') as fp:
    exec(fp.read(), None, _locals)
version = _locals['__version__']

setup(
    name="autocore",
    version=version,
    description="A lightweight distributed networking package",
    long_description=longdesc,
    author="Jonathan Hanna",
    author_email="business@jonathan-hanna.com",
    url="https://github.com/JonathanHanna/Autocore/",
    packages=['autocore'],
    license='Apache Software License',
    platforms='any',  # is this true?
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Robotics :: RoboticsMiddleware',
        'Topic :: Software Development :: Networking',
    ],
)
