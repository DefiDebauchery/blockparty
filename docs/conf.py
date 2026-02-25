import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

"""Sphinx configuration for blockparty docs."""

project = "blockparty"
copyright = "2026, blockparty contributors"
author = "DefiDebauchery"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

# Theme
html_theme = "furo"
html_title = "blockparty"

# Autodoc
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_class_signature = "separated"

# Napoleon (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_attr_annotations = True

# Intersphinx (link to Python/Pydantic docs)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
}

# Suppress noisy warnings from Pydantic model fields
nitpicky = False
