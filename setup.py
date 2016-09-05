from distutils.core import setup
from setuptools import find_packages

setup(
    name='rosreestr2coord',
    version='1.0.1',
    # scripts=['rosreestr2coord.py'],
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='Get geometry from rosreestr',
    long_description='Get area coordinates by its cadastral number',
    install_requires=['numpy'],
    url='https://github.com/rendrom/rosreestr2coord',
    author='Artemiy Doroshkov',
    author_email='rendrom@gmail.com',
    entry_points={
        'console_scripts': [
            'rosreestr2coord=script.rosreestr2coord:main',
        ],
    },
)
