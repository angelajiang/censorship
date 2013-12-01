"""
Package setup template script.

Author: John Otto <jotto@eecs.northwestern.edu>
"""

from setuptools import setup
import sys

if not sys.argv[-1] == "bdist_egg":
    sys.argv.append("bdist_egg")

# TODO: specify the package
module = __import__("censorship")

setup(
    name = module.__name__,
    version = module.__version__,
    packages = [module.__name__],
    
    # TODO: include author information
    #author = "",
    #author_email = "",

    # TODO: list all packages that are directly referenced
    install_requires=[],

    # Note: this list is parsed by the scripts in
    #   projects/server-package-manager to inform clients of
    #   inter-package dependencies. When testing, you are
    #   responsible for making sure all packages are present
    #   and initialized.
)
