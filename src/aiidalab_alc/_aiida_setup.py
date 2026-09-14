"""Shared setup for the gallery examples (not itself a gallery item).

sphinx-gallery adds the tutorials directory to ``sys.path`` while executing
examples, so each ``plot_*.py`` can ``from _aiida_setup import ...``. This module
is excluded from the gallery via ``ignore_pattern`` in ``conf.py``.

Importing it makes the docs build hermetic: it points ``AIIDA_PATH`` at a fresh
throwaway directory and creates an empty config there *before* anything imports
aiida-pythonjob (which reads the config at import time). It then provides helpers
to load an in-memory profile + localhost code, locate bundled sample data, and
display AiiDA provenance graphs.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Redirect AiiDA config to an ephemeral dir *before* importing aiida, so the docs
# build never reads or writes a real ``~/.aiida`` and aiida-pythonjob's import-time
# ``get_config()`` succeeds on a fresh machine (e.g. CI). Mirrors tests/conftest.py.
os.environ["AIIDA_PATH"] = tempfile.mkdtemp(prefix="aiida-docs-config-")

import matplotlib.pyplot as plt
from aiida import load_profile, orm
from aiida.common.exceptions import NotExistent
from aiida.manage.configuration import get_config
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.visualization import Graph

get_config(create=True)

# tests/data holds the bundled sample inputs (CASTEP, Phonopy). Located relative
# to this file: docs/source/tutorials/ -> repository root is three parents up.
_DATA_DIR = Path(__file__).resolve().parents[2] / "tests" / "data"


def example_data(*parts: str) -> str:
    """Absolute path to a bundled sample-data file under ``tests/data``."""
    return str(_DATA_DIR.joinpath(*parts))


def get_python_code():
    """Load an in-memory AiiDA profile and return a localhost Python ``Code``.

    Uses an in-memory SQLite profile (no PostgreSQL, no persistent config) and a
    ``core.direct`` localhost computer running this interpreter -- enough to
    execute PythonJobs during the docs build.
    """
    # `runner.poll.interval` defaults to 60 s, and a WorkChain awaiting a child
    # process (`self.submit` + `ToContext`) pays it once per child -- turning a
    # seconds-long example into a minutes-long one. AiiDA waives it for *test*
    # profiles (`Manager.create_runner`: `poll_interval = 0.0 if
    # profile.is_test_profile else ...`), which is why the pytest suite never sees
    # this, but a profile built here is not flagged as one. Setting the option on
    # the profile is the supported route: profile options take priority over the
    # config and the built-in default (`Manager.get_option`).
    load_profile(
        SqliteTempBackend.create_profile(
            "pythonjob-ins-docs", options={"runner.poll.interval": 0}
        ),
        allow_switch=True,
    )

    try:
        computer = orm.load_computer("localhost")
    except NotExistent:
        computer = orm.Computer(
            label="localhost",
            hostname="localhost",
            transport_type="core.local",
            scheduler_type="core.direct",
            workdir=tempfile.mkdtemp(),
        ).store()
        computer.configure(safe_interval=0.0)

    try:
        return orm.load_code("python3@localhost")
    except NotExistent:
        return orm.InstalledCode(
            computer=computer,
            label="python3",
            filepath_executable=sys.executable,
            default_calc_job_plugin="pythonjob.pythonjob",
        ).store()


def show_provenance(
    node,
    title: str = "Provenance graph",
    max_width_inches: float = 12.0,
    dpi: int = 100,
):
    """Display the provenance graph around ``node`` as a matplotlib figure.

    Traverses **both** directions, because either alone tells half the story:

    * ``recurse_descendants`` -- what the process *did*: the steps it called and
      the data handed between them. Without this a ``WorkChain`` renders as a
      single opaque box, since its called steps are descendants (via ``CALL``
      links), not ancestors.
    * ``recurse_ancestors`` -- where its inputs came from. Usually just the input
      nodes, but an input may itself have been produced by an earlier
      calculation (as the Phonopy example's force constants are), and that
      history is worth showing.

    Laid out top-to-bottom: these graphs are chains of a few steps, so
    left-to-right makes them extremely wide (11:1 for the nested TOSCA workflow)
    and the labels unreadable once scaled into a figure.

    Renders to a PNG and shows it via ``imshow`` so sphinx-gallery captures it
    like any other figure.
    """
    graph = Graph()
    graph.recurse_ancestors(node, annotate_links="both")
    graph.recurse_descendants(node, annotate_links="both")
    graph.graphviz.attr(rankdir="TB")
    with tempfile.TemporaryDirectory() as tmpdir:
        png = graph.graphviz.render(f"{tmpdir}/provenance", format="png", cleanup=True)
        image = plt.imread(png)

    # Size the figure from the rendered image rather than fixing it: a fixed
    # figsize squeezes a large graph until its labels are illegible. Pixels map
    # roughly 1:1 up to ``max_width_inches``, beyond which the graph is scaled
    # down to fit the page.
    height, width = image.shape[:2]
    scale = min(1.0, max_width_inches * dpi / width)
    fig, ax = plt.subplots(figsize=(width * scale / dpi, height * scale / dpi), dpi=dpi)
    ax.imshow(image)
    ax.set_axis_off()
    ax.set_title(title)
    fig.tight_layout()
    return fig