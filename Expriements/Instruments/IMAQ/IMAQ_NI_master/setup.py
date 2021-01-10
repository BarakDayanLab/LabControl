from setuptools import setup, find_packages

import IMAQ_NI as imq

setup(
    name="IMAQ_NI",
    version=imq.__version__,
    description="Python bindings to IMAQ NI API.",
    author="Assaf Shonfeld",
    author_email="",
    url="",
    packages=find_packages()
)
