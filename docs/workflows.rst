Workflows
=========

The app's main model, :class:`~aiidalab_alc.main_process.MainAppModel`,
listens for the **Submit** button in the computational resources step. It
then picks a workflow based on the ``data_type`` set in the data input step:

.. list-table::
   :header-rows: 1

   * - ``data_type``
     - Set by
     - Process class
   * - ``ase_mlip``
     - Submitting a structure
     - :class:`~aiidalab_alc.mlip_process.MLIPProcess`
   * - ``phonopy`` / ``castep``
     - Submitting force constants
     - :class:`~aiidalab_alc.ins_process.INSProcess`

When the process has finished, its outputs are stored on the
:class:`~aiidalab_alc.results.ResultsModel` and the **Results** step is
unlocked.

.. code-block:: text

   Data Input ──► Configure Workflow ──► Computational Resources ──► Results
       │                                          │
       │ data_type                                │ submitted
       ▼                                          ▼
   ase_mlip ─────────────► MLIPProcess ──┐
   phonopy / castep ──────► INSProcess ──┴──► ResultsModel

.. _mlip-workflow:

MLIP workflow
-------------

Implemented in :class:`~aiidalab_alc.mlip_process.MLIPProcess`. The
calculation is built as an `aiida-workgraph
<https://aiida-workgraph.readthedocs.io/>`_ ``WorkGraph`` named
``GeomOptGraph`` with two tasks:

1. **geomopt_calc** — an ``aiida-mlip`` calculation (``mlip.opt``) that
   relaxes the input structure with the chosen MLIP model. Its inputs are the
   model (a ``ModelData`` node loaded from the local model file), the device,
   ``fmax`` and either ``opt_cell_lengths`` or ``opt_cell_fully``. If DFT-D3
   is enabled, ``calc_kwargs={"dispersion": True}`` is added.
2. **ph_calc** — an ``aiida-mlip`` phonon calculation (``mlip.ph``) on the
   optimised structure (``final_structure``), using:

   * ``supercell`` — from the phonon parameters (e.g. ``"2 2 2"``)
   * ``displacement = 0.01``
   * ``n_qpoints = 51``
   * ``bands``, ``dos`` and ``pdos`` all enabled

The WorkGraph runs in the notebook's kernel. When it has finished, the
following are stored on the results model:

* the final structure (from the optimisation ``results_dict``)
* the phonon band structure (from the compressed Phonopy ``bands.yml.xz``,
  converted to a ``BandsData`` node)
* the DOS (converted to an ``XyData`` node) and the PDOS (raw text)
* the Phonopy results dictionary, used for the Phonopy YAML export

.. _ins-workflow:

INS workflow
------------

Implemented in :class:`~aiidalab_alc.ins_process.INSProcess`, using work
chains from ``aiida_pythonjob_ins`` (provided by ``aiida-alc-ins``). These
run `Euphonic <https://euphonic.readthedocs.io/>`_ inside AiiDA
``PythonJob`` calculations on a ``python3@localhost`` code, which is created
automatically by :func:`~aiidalab_alc.ins_process.get_python_code` if needed.

The input is a ``ForceConstantsData`` node built from the Phonopy YAML or
CASTEP ``.castep_bin`` file.

1. **DispersionWorkChain** — calculates the phonon band structure at the
   requested q-spacing. Output: ``band_structure``.
2. **DosWorkChain** — calculates the phonon density of states at the
   requested q-spacing and energy spacing. Output: ``dos``.
3. **ToscaFromForceConstantsWorkChain** *(optional)* — simulates the INS
   spectrum for the TOSCA spectrometer (detector angle 135°). Output:
   ``spectrum``.

If any work chain exits with a non-zero status, the workflow stops and the
exit status is printed.

.. _current-limitations:

Current limitations
-------------------

The app is still in active development (version |release|). The following
options appear in the interface but are not yet fully passed to the
calculations:

* **MLIP:** ``Pressure``, ``Number of points``, ``Auto bands calculation``,
  ``No. CPUs``, ``Process Label`` and ``Description`` are not yet passed on.
  The phonon calculation always uses 51 q-points and a displacement of 0.01 Å.
* **MLIP:** the ``atoms only`` optimisation option is currently treated the
  same as ``fully relax``.
* **MLIP:** choosing ``Single point`` currently still runs the ``mlip.opt``
  calculation as the first task of the WorkGraph.
* **INS:** temperature, the RESINS/TOSCA spacings and the supercell (MP grid)
  sampling mode are stored but not yet used.
* Workflows run in the notebook's kernel (``run`` / ``run_get_node``)
  rather than being sent to the AiiDA daemon.
