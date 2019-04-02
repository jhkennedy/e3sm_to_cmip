# coding=utf-8
from setuptools import find_packages, setup

setup(
    name="e3sm_to_cmor",
    version="1.1.0",
    author="Sterling Baldwin",
    author_email="baldwin32@llnl.gov",
    description="Transform E3SM model data output into cmip6 compatable data "
                "using the Climate Model Output Rewriter.",
    install_requires=['cdms2',
                      'cdutil',
                      'cmor',
                      'numpy'],
    entry_points={'console_scripts':
                  ['e3sm_to_cmip = e3sm_to_cmip.__main__:main']},
    packages=find_packages(),
    zip_safe=False)
