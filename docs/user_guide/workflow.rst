Step 2: Configure Workflow
==========================

The options in this step depend on what was submitted in
:doc:`data_input`. If nothing has been submitted yet, the step shows
*"Select structure or force constants"*.

.. _mlip-options:

MLIP calculation (structure input)
----------------------------------

The **MLIP Calculation** panel has two tabs.

MLIP Parameters
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Description
   * - Calculation
     - Geometry optimisation
     - ``Single point`` or ``Geometry optimisation``.
   * - Optimisation
     - cell lengths
     - What is relaxed during a geometry optimisation: ``cell lengths``,
       ``fully relax`` or ``atoms only``. Disabled for single points.
   * - Use DFTd3
     - off
     - Add a DFT-D3 dispersion correction to the MLIP energies and forces.
   * - Pressure
     - 0.0
     - External pressure for the optimisation. Disabled for single points.
   * - Max force
     - 0.001
     - Force convergence criterion (``fmax``) for the optimisation.
       Disabled for single points.
   * - Architecture
     - mace
     - The MLIP architecture.
   * - Model filename
     - ``mace_mp_small.model``
     - Path to the MLIP model file on the server. Required.

Phonon Parameters
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Description
   * - Supercell size in x / y / z
     - 2 / 2 / 2
     - Supercell used for the finite displacement phonon calculation (1–10).
   * - Number of points
     - 51
     - Number of q-points along the band structure path.
   * - Auto bands calculation
     - on
     - Generate the band structure path automatically.

Click **Submit Options** to confirm. If no model file has been given, an
error is shown and the options are not submitted.

.. _ins-options:

INS calculation (force constant input)
--------------------------------------

The **INS Calculation** panel first asks how the q-point sampling is set,
using the **INS options** radio buttons:

* **Use spacing** (default) — set a q-point spacing.
* **Use supercell size** — set a Monkhorst–Pack grid (``MP grid in x/y/z``).

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Option
     - Default
     - Description
   * - q-spacing
     - 0.1
     - Maximum q-point spacing used for the dispersion and DOS.
   * - Temperature, K
     - 300
     - Temperature used for the calculation.
   * - Energy Spacing for DOS
     - 1.0
     - Width of the energy bins for the density of states.
   * - q-spacing RESINS/TOSCA
     - 1.0
     - q-point spacing for the TOSCA spectrum calculation.
   * - Energy Spacing RESINS/TOSCA
     - 5.0
     - Width of the energy bins for the TOSCA spectrum.
   * - band structure calculation
     - on
     - The phonon dispersion is always calculated.
   * - Calculate RESINS/TOSCA
     - off
     - Also simulate an INS spectrum for the TOSCA spectrometer.

Click **Submit INS Options** to confirm.

.. note::

   Only **q-spacing** and **Energy Spacing for DOS** are currently passed to
   the dispersion and DOS work chains. The TOSCA work chain uses a fixed
   q-spacing of 1.0, an energy spacing of 5.0 and a detector angle of 135°.
   The temperature, the RESINS/TOSCA spacings and the MP grid settings are
   stored on the model but are not yet used. See
   :ref:`current-limitations`.
