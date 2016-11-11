# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('ispaq/ispaq.py').read(),
    re.M
    ).group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "cmdline-ispaq",
    packages = ["ispaq"],
    entry_points = {
        "console_scripts": ['ispaq = ispaq.ispaq:main']
        },
    version = version,
    description = "IRIS System for Portable Assessment of Quality (ISPAQ)",
    long_description = long_descr,
    author = "Jonathan Callahan",
    author_email = "jonathan@mazamascience.com",
    url = "http://github.com/iris-edu/ispaq",
    )
