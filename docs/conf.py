"""Sphinx configuration for the AiiDAlab ALC INS documentation."""

import configparser
import importlib.metadata
import shutil
import sys
from datetime import datetime
from pathlib import Path

DOCS_DIR = Path(__file__).parent.resolve()
ROOT_DIR = DOCS_DIR.parent

# Make the python package importable for autodoc without installing it.
sys.path.insert(0, str(ROOT_DIR / "src"))

# ``aiidalab_alc/__init__.py`` reads its version from the installed package
# metadata. Fall back to the version in setup.cfg when building the docs from
# a source checkout where the package has not been pip-installed.
_metadata_version = importlib.metadata.version


def _version_with_fallback(distribution_name: str) -> str:
    try:
        return _metadata_version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        if distribution_name == "aiidalab-alc-app":
            return release
        raise


importlib.metadata.version = _version_with_fallback

# -- Project information -----------------------------------------------------

_setup_cfg = configparser.ConfigParser()
_setup_cfg.read(ROOT_DIR / "setup.cfg")

project = "AiiDAlab ALC INS"
author = _setup_cfg.get("metadata", "author", fallback="John Purton").strip()
copyright = f"{datetime.now().year}, Ada Lovelace Centre (STFC)"
release = _setup_cfg.get("metadata", "version", fallback="0.0.1").strip()
version = release

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "numpydoc",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The heavy scientific / AiiDA stack is not required to build the docs. Mock
# these imports so autodoc can import the package in a lightweight environment.
autodoc_mock_imports = [
    "aiida",
    "aiida_mlip",
    "aiida_pythonjob",
    "aiida_pythonjob_ins",
    "aiida_workgraph",
    "aiidalab_widgets_base",
    "alc_aiidalab_widgets",
    "ase",
    "euphonic",
    "h5py",
    "IPython",
    "ipywidgets",
    "numpy",
    "phonopy",
    "plotly",
    "traitlets",
    "yaml",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autosummary_generate = True

numpydoc_show_class_members = False
numpydoc_validation_checks = set()

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiida": ("https://aiida.readthedocs.io/projects/aiida-core/en/stable/", None),
    "ipywidgets": ("https://ipywidgets.readthedocs.io/en/stable/", None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = "piccolo_theme"
html_title = f"{project} v{release}"
html_static_path = ["_static"]
html_logo = "_static/alc.svg"
html_favicon = "_static/alc-100.png"
html_theme_options = {
    "source_url": "https://github.com/jap93/aiidalab-alc-ins",
    "source_icon": "github",
}

# Re-use the logo images shipped with the app rather than duplicating them.
_static_dir = DOCS_DIR / "_static"
_static_dir.mkdir(exist_ok=True)
for _img in ("alc.svg", "alc-100.png"):
    _src = ROOT_DIR / "images" / _img
    if _src.exists():
        shutil.copy2(_src, _static_dir / _img)
