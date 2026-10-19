AiiDAlab ALC INS
================

.. image:: _static/alc.svg
   :alt: Ada Lovelace Centre logo
   :width: 300px
   :align: center

|

**AiiDAlab ALC INS** is an `AiiDAlab <https://www.aiidalab.net/>`_ application,
developed at the Ada Lovelace Centre (STFC), that provides a graphical,
notebook-based interface for running **machine-learned interatomic potential
(MLIP)** and **phonon** calculations, and for simulating **inelastic neutron
scattering (INS)** spectra.

All calculations are run through `AiiDA <https://www.aiida.net/>`_, so every
step of a workflow is stored with full data provenance.

Features
--------

* **MLIP calculations** — single point energies and geometry optimisations
  using `MACE <https://github.com/ACEsuit/mace>`_ models via
  `aiida-mlip <https://github.com/stfc/aiida-mlip>`_ and
  `janus-core <https://github.com/stfc/janus-core>`_, with optional DFT-D3
  dispersion corrections.
* **Phonon calculations** — finite displacement phonons (via phonopy) on the
  optimised structure, giving phonon dispersions, the density of states (DOS)
  and the projected DOS.
* **INS from existing force constants** — import force constants from
  **Phonopy** (``phonopy.yaml``) or **CASTEP** (``.castep_bin``) and compute
  phonon dispersions, DOS and simulated **TOSCA** spectra with
  `Euphonic <https://euphonic.readthedocs.io/>`_ via
  ``aiida-pythonjob-ins``.
* **Interactive results** — 3D structure viewer, interactive phonon band
  structure and DOS/spectrum plots, and export of results to plain-text and
  Phonopy YAML files.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/index

.. toctree::
   :maxdepth: 2
   :caption: Reference

   workflows
   api/index

.. toctree::
   :maxdepth: 1
   :caption: Development

   developer

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

