from distutils.core import setup
from setuptools import find_packages

from script.parser import VERSION

setup(
    name='rosreestr2coord',
    version=VERSION,
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='Get geometry from rosreestr',
    long_description='Get area coordinates by its cadastral number',
    install_requires=[],
    url='https://github.com/rendrom/rosreestr2coord',
    author='Artemiy Doroshkov',
    author_email='rendrom@gmail.com',
    entry_points={
        'console_scripts': [
            'rosreestr2coord=script.console:main',
        ],
    },
)
