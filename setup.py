from distutils.core import setup
from setuptools import find_packages

from scripts.parser import VERSION

setup(
    name='rosreestr2coord',
    version=VERSION,
    packages=find_packages(exclude=['tests*']),
    zip_safe=False,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        # 'Intended Audience :: Developers',
        # 'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
    ],
    description='Get geometry from rosreestr',
    long_description='Get area coordinates by its cadastral number',
    install_requires=["numpy"],
    url='https://github.com/rendrom/rosreestr2coord',
    author='Artemiy Doroshkov',
    author_email='rendrom@gmail.com',
    entry_points={
        'console_scripts': [
            'rosreestr2coord=scripts.console:main',
        ],
    },
)
