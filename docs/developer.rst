Developer Guide
===============

Development install
-------------------

.. code-block:: bash

   git clone https://github.com/jap93/aiidalab-alc-ins.git
   cd aiidalab-alc-ins
   pip install -e ".[dev]"

Code style
----------

The project uses `ruff <https://docs.astral.sh/ruff/>`_ for linting and import
sorting (see ``[tool.ruff]`` in ``pyproject.toml``). Docstrings follow the
**numpy** convention:

.. code-block:: bash

   ruff check src

Tests
-----

Test data is kept in ``tests/data``:

* ``NaCl-traj.xyz`` — an NaCl structure / trajectory
* ``mace_mp_small.model`` — a small MACE-MP model
* ``phonopy_data.yaml`` — Phonopy data with force constants
* ``quartz.castep_bin`` — CASTEP force constants for quartz

Run the tests with:

.. code-block:: bash

   pytest

Project layout
--------------

.. code-block:: text

   aiidalab-alc-ins/
   ├── main.ipynb              # App entry notebook
   ├── start.py                # AiiDAlab home-page start banner
   ├── images/                 # Logos used by the app
   ├── docker/                 # Dockerfile and container start-up script
   ├── docs/                   # This documentation
   ├── src/aiidalab_alc/
   │   ├── main.py             # MainApp, MainAppView, WizardWidget
   │   ├── main_process.py     # MainAppModel: dispatches workflows
   │   ├── data.py             # Step 1: structure / force constants input
   │   ├── workflow.py         # Step 2: MLIP, phonon and INS options
   │   ├── resources.py        # Step 3: code and resources
   │   ├── results.py          # Step 4: results viewer and downloads
   │   ├── mlip_process.py     # MLIP + phonon WorkGraph
   │   ├── ins_process.py      # Euphonic INS work chains
   │   ├── utils.py            # Helper functions
   │   └── common/             # Reusable widgets
   └── tests/data/             # Example input files

Architecture
------------

The app follows a model–view pattern:

* **Models** are ``traitlets.HasTraits`` classes
  (:class:`~aiidalab_alc.data.DataStepModel`,
  :class:`~aiidalab_alc.workflow.WorkflowCalculationModel`,
  :class:`~aiidalab_alc.resources.ComputationalResourcesModel`,
  :class:`~aiidalab_alc.results.ResultsModel`). They are owned by
  :class:`~aiidalab_alc.main_process.MainAppModel`.
* **Views** are ``ipywidgets`` containers that also inherit from
  ``aiidalab_widgets_base.WizardAppWidgetStep``. Widget values are kept in
  sync with model traits using ``traitlets.link`` / ``ipywidgets.dlink``.
* Each view builds its widgets lazily in ``render()``, which is called when
  its wizard step is opened.

Building the documentation
--------------------------

Install the documentation requirements and build the HTML pages:

.. code-block:: bash

   pip install -r docs/requirements.txt
   cd docs
   make html

The HTML output is written to ``docs/_build/html``; open
``docs/_build/html/index.html`` in a browser. The heavy AiiDA and scientific
dependencies are mocked in ``docs/conf.py``, so the full app stack is not
needed to build the docs.

