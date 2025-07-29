import os
import sys

project = "macrotype"

# Ensure package can be imported
sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

html_theme = "sphinx_rtd_theme"


def setup(app):
    pass
