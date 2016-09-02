#!/usr/bin/env python

from setuptools import setup


setup(name='ilamb',
      description='ESM/ILAMB Wrapper',
      author='Sheri Mickelson',
      author_email='mickelso@ucar.edu',
      packages=['ilamb'],
      scripts=['ilamb/cesm_ilamb_generator.py', 'ilamb/clm_to_mip'],
      install_requires=[]
      )
