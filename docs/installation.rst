Installation
============

There are two main ways to use the application: run the pre-configured
Docker image, or install the app into an existing AiiDAlab environment.

Requirements
------------

* Python 3.10 (the app builds the ``ghcr.io/stfc/alc-ux/base:py310`` image)
* An AiiDA profile with a configured ``localhost`` computer
* The following AiiDA plugins and libraries:

  * ``aiida-core`` and ``aiidalab-widgets-base``
  * `aiida-mlip <https://github.com/stfc/aiida-mlip>`_ (MLIP / phonon
    calculations; installed via ``aiida-mlip-phonon``)
  * `aiida-alc-ins <https://github.com/stfc/aiida-alc-ins>`_
    (provides ``aiida_pythonjob_ins`` for INS work chains)
  * ``aiida-workgraph`` and ``aiida-pythonjob``
  * ``euphonic``, ``phonopy``, ``ase``, ``h5py`` and ``plotly``

* For MLIP calculations: the ``janus`` executable (from ``janus-core``) on
  the ``PATH`` and ``mace-torch`` with a MACE model file
  (e.g. ``mace_mp_small.model``).

Using Docker
------------

A ``Dockerfile`` is provided in the ``docker/`` directory. It builds on the
ALC AiiDAlab base image, installs the required AiiDA plugins, and copies the
application into ``/home/jovyan/apps/aiidalab-alc-ins``. 

The image can be built from the repository root, where the whole
repository is copied into the image:

.. code-block:: bash

   git clone https://github.com/jap93/aiidalab-alc-ins.git
   cd aiidalab-alc-ins
   docker build -f docker/Dockerfile -t aiidalab-alc-ins .

Then run the container and open the URL printed in the terminal:

.. code-block:: bash

   docker run -it -p 8888:8888 aiidalab-alc-ins

.. note::

   ``mace-torch`` is **not** installed in the image by default as it
   makes the image very large (>10 GB) and slow to build. Install it from a
   terminal inside the running container:

   .. code-block:: bash

      pip install mace-torch


