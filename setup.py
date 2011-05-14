from setuptools import setup

execfile('src/cfm/_version.py')
setup(name="cfm",
    version=__version__,
    author='Jake Hickenlooper',
    author_email='jake.hickenlooper@gmail.com',
    description="Cruddy File Management",
    packages=['cfm'],
    package_dir={'': 'src'},
    install_requires=[
      'python-cloudfiles',
      'progressbar',
      ],
    include_package_data = True,
    entry_points=("""
      [console_scripts]
      cloudfile=cfm:main
      cloudinfo=cfm:info
      """)
    )
