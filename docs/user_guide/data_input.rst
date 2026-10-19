Step 1: Data Input
==================

The **Data Input** step has two collapsible panels: **Structure** and
**Force Constants**. Fill in *one* of them. The panel you submit decides
which workflow runs later (see :doc:`../workflows`).

Structure
---------

Use this panel to start an :ref:`MLIP workflow <mlip-workflow>` from an
atomic structure.

There are two tabs:

**Upload File**
   Upload a structure file from your computer. Any format that
   `ASE <https://wiki.fysik.dtu.dk/ase/ase/io/io.html>`_ can read is accepted
   (e.g. ``.xyz``, ``.extxyz``, ``.cif``, ``POSCAR``, ``.cell``). If the file
   holds several frames (a trajectory), the first frame is used.

**AiiDA Database**
   Choose a ``SinglefileData`` node that is already stored in your AiiDA
   database.

Once the file has been read, the structure appears in the **Viewer**. If the
structure cannot be read, the viewer shows *"Could not visualise structure
from file..."*.

Click **Submit Structure** to confirm. This locks the inputs and selects the
MLIP workflow.

Force Constants
---------------

Use this panel to start an :ref:`INS workflow <ins-workflow>` from force
constants you have already calculated. Choose the **Input Method**:

``phonopy``
   Upload a Phonopy YAML file (e.g. ``phonopy.yaml`` or
   ``phonopy_data.yaml``). The file must contain:

   * a ``unit_cell`` (or ``primitive_cell``) with ``lattice`` and ``points``,
     from which the crystal structure is built, and
   * a ``force_constants`` block.

   Phonopy files exported from the :doc:`results` step of an MLIP calculation
   meet these requirements.

``castep``
   Browse to a CASTEP ``.castep_bin`` file on the server's file system. The
   force constants and crystal structure are read with Euphonic.

Click **Submit Force Constants** to confirm. The button label changes to show
which format was submitted.

.. note::

   Force constants are parsed into an ``aiida_pythonjob_ins``
   ``ForceConstantsData`` node. If the file has no force constants, or no
   cell for the structure, a ``ValueError`` is raised with a description of
   what is missing.

