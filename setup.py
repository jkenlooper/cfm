from setuptools import setup, find_packages
import os

name = "cfm"
execfile('src/cfm/_version.py')

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name=name,
    version=__version__,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    description="Cruddy File Management for rackspace cloudfiles",
    long_description=read('README.rst'),
    url='http://www.weboftomorrow.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.6',
        ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'setuptools',
        'python-cloudfiles',
        'progressbar',
      ],
    include_package_data = True,
    entry_points="""
      [console_scripts]
      cloudfile=cfm:main
      cloudinfo=cfm:info
      """
    )
