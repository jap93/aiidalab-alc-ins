Step 3: Configure Computational Resources
=========================================

This step picks the AiiDA code that runs the calculation and labels the
AiiDA process that will be created. Clicking **Submit** here **starts the
calculation**.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Description
   * - Code
     - The AiiDA code used for MLIP calculations. The list shows every code
       in the AiiDA database; click **Refresh** to update it.
   * - Device
     - ``cpu`` or ``cuda`` (GPU). The device the MLIP model runs on.
   * - No. CPUs
     - Number of CPUs (1–128). Only used with the ``cpu`` device.
   * - Process Label
     - A short label for the AiiDA process. **Required.**
   * - Description
     - An optional longer description of the process.

Automatic Janus code setup
--------------------------

When this step loads, the app tries to create a ``janus@localhost``
``InstalledCode`` for the ``janus.janus`` plugin:

* If the ``janus`` executable is not on the ``PATH``, the message
  *"Janus executable was not found on PATH"* is shown.
* If the AiiDA computer ``localhost`` is not configured, the message
  *"AiiDA computer 'localhost' is not configured"* is shown.
* Otherwise the code is created (if it does not already exist) and selected.

INS workflows do not use the selected code. They run as AiiDA
``PythonJob`` calculations on a ``python3@localhost`` code, which is
created automatically from the current Python interpreter if it does not
exist.

Validation
----------

If no code is selected or the process label is empty, a validation error is
shown and the calculation is not submitted. If the ``aiida-mlip`` plugin
cannot be imported, the **Submit** button is disabled and a warning is shown.

.. important::

   Calculations are currently run in the notebook's kernel (not sent to the
   AiiDA daemon), so the notebook stays busy until the workflow finishes.

