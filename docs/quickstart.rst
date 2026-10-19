Quick Start
===========

Launching the app
-----------------

Open the app from the AiiDAlab home page, or open ``main.ipynb`` from the
app directory. The notebook loads the default AiiDA profile and creates the
application:

.. code-block:: python

   from aiida import load_profile
   load_profile()

   from aiidalab_alc.main import MainApp
   app = MainApp()

The app is laid out as a four-step wizard:

1. **Data Input** — provide a structure *or* a set of force constants.
2. **Configure Workflow** — set the calculation parameters.
3. **Configure Computational Resources** — choose the code, device and
   number of CPUs, and label the process.
4. **Results** — view and download the results.

Each step has a green **Submit** button that confirms its settings. Once a
step is submitted its inputs are locked. To start again, click
**New Calculation** at the top of the page.

Which path should I use?
------------------------

The data you provide in step 1 decides which workflow runs:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Input in step 1
     - Workflow
     - Outputs
   * - Structure file (``Structure`` panel)
     - :ref:`MLIP workflow <mlip-workflow>`: optimisation / single point
       followed by a phonon calculation
     - Final structure, phonon dispersion, DOS, PDOS, Phonopy data
   * - Phonopy or CASTEP force constants (``Force Constants`` panel)
     - :ref:`INS workflow <ins-workflow>`: Euphonic dispersion, DOS and
       optional TOSCA spectrum
     - Structure, phonon dispersion, DOS, TOSCA spectrum

Example: MLIP phonons for NaCl
------------------------------

1. In **Data Input**, open the **Structure** panel, upload
   ``tests/data/NaCl-traj.xyz`` and click **Submit Structure**.
2. In **Configure Workflow**, keep *Geometry optimisation* with
   *cell lengths*, and set the **Model filename** to a MACE model
   (e.g. ``tests/data/mace_mp_small.model``). Set the supercell in the
   **Phonon Parameters** tab and click **Submit Options**.
3. In **Configure Computational Resources**, check that the ``janus`` code is
   selected, enter a **Process Label** and click **Submit**.
4. Open **Results** to view the optimised structure, phonon dispersion and
   density of states.

Example: INS from Phonopy force constants
-----------------------------------------

1. In **Data Input**, open the **Force Constants** panel, select
   ``phonopy`` as the input method, upload ``tests/data/phonopy_data.yaml``
   and click **Submit Force Constants**.
2. In **Configure Workflow**, set the q-spacing, temperature and DOS energy
   spacing. Tick **Calculate RESINS/TOSCA** to also simulate a TOSCA spectrum,
   then click **Submit Options**.
3. In **Configure Computational Resources**, enter a **Process Label** and
   click **Submit**.
4. Open **Results** to view the dispersion, DOS and TOSCA spectrum.

