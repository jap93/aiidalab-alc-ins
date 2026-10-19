Step 4: Results
===============

When the workflow has finished, the **Results** step shows the UUID of the
AiiDA process and a set of tabs.

Result tabs
-----------

**Resulting Structure**
   An interactive 3D view of the final structure: the optimised structure
   for MLIP workflows, or the structure read from the force constants for
   INS workflows.

**Phonon Dispersion**
   An interactive plot of the phonon band structure along the high-symmetry
   path.

**Density of States**
   The phonon density of states plotted against energy.

**TOSCA Spectrum**
   The simulated INS spectrum for the TOSCA spectrometer. This is only shown
   if **Calculate RESINS/TOSCA** was ticked in an INS workflow.

**Download Options**
   Tick the results to save, then click **Download Results**.

Downloading results
-------------------

Files are written to the notebook's working directory (normally the app
directory):

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Option
     - File
     - Contents
   * - Bands
     - ``bands_data.dat``
     - Phonon frequencies at each q-point (one row per q-point).
   * - DoS
     - ``dos_data.dat``
     - Two columns: energy and density of states, with units in the header.
   * - PDOS
     - ``pdos_data.dat``
     - Projected density of states (MLIP workflow only).
   * - Phonopy (with force constants)
     - ``phonopy_data.yaml``
     - Phonopy data including the full force constant matrix (MLIP
       workflow only). Can be loaded back into the app as
       :doc:`Force Constants <data_input>` input to run an INS workflow.
   * - TOSCA Spectrum
     - ``ins_spectrum.dat``
     - Two columns: energy and intensity.

.. tip::

   The MLIP workflow also writes ``force_constants.hdf5`` and
   ``bands.yml.xz`` to the working directory. The Phonopy export reads
   ``force_constants.hdf5``, so do not delete it before downloading.

