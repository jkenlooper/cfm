from setuptools import setup

setup(name="cfm",
    version='0.1.0',
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
      """)
    )
      #cloudinfo=cfm:info
