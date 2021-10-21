# -*- coding: utf-8 -*-
"""
Created on Mon May 25 12:05:42 2020

@author: ozkan
"""
import numpy
from distutils.core import setup
from Cython.Build import cythonize

setup(package_dir={'cython': ''},
      ext_modules = cythonize('run_cython.pyx'),
      include_dirs=[numpy.get_include()])