from setuptools import setup, Extension
from wheel.bdist_wheel import bdist_wheel
from os.path import join as pjoin
import sys

class bdist_wheel_abi3(bdist_wheel):
    def get_tag(self):
        python, abi, plat = super().get_tag()

        if python.startswith("cp"):
            # on CPython, our wheels are abi3 and compatible back to 3.6
            return "cp37", "abi3", plat

        return python, abi, plat

def get_version():
    fn = pjoin('src','_rl_accel.c')
    try:
        with open(fn,'r') as _:
            for l in _.readlines():
                if l.startswith('#define'):
                    l = l.split()
                    if l[1]=='VERSION':
                        return eval(l[2],{})
    except:
        raise ValueError('Cannot determine _rl_accel Version')

setup(
    ext_modules=[
        Extension(
            "_rl_accel",
            sources=[pjoin('src','_rl_accel.c')],
            define_macros=[("Py_LIMITED_API", "0x03070000")],
            py_limited_api=True,
        )
    ],
    name="rl_accel",
    version=get_version(),
    license="BSD license (see _rl_accel-licens.txt for details), Copyright (c) 2000-2022, ReportLab Inc.",
    description="Acclerator for ReportLab",
    long_description="""This is an accelerator module for the ReportLab Toolkit Open Source Python library for generating PDFs and graphics.""",
    author="Andy Robinson, Robin Becker, the ReportLab team and the community",
    author_email="reportlab-users@lists2.reportlab.com",
    url="http://www.reportlab.com/",
    packages=[],
    package_data = {},
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Topic :: Printing',
        'Topic :: Text Processing :: Markup',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        ],
    license_files = ['LICENSE.txt'],
            
    #this probably only works for setuptools, but distutils seems to ignore it
    install_requires=[],
    python_requires='>=3.7,<4',
    extras_require={
        },
    cmdclass={"bdist_wheel": bdist_wheel_abi3},
)
