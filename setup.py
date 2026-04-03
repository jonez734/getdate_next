#!/usr/bin/env python3

import os
import time
from setuptools import setup

projectname = "getdate-next"

v = os.environ.get("VERSION")
if v is None:
    v = time.strftime("%Y%m%d%H%M")

setup(
    name=projectname,
    version=v,
    author="zoidtechnologies.com",
    author_email="%s@projects.zoidtechnologies.com" % (projectname),
    license="GPLv2+",
    url="https://github.com/zoidtechnologies/getdate-next",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: POSIX",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v2+ (GPLv2+)",
    ],
    packages=["getdate_next"],
    package_data={"getdate_next": []},
)
