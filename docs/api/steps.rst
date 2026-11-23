Wizard Steps
============

Each wizard step is built from a *model* (a ``traitlets.HasTraits`` class
that holds the step's state) and one or more *views* (``ipywidgets``
widgets that display and edit the model). Models live in
``aiidalab_alc.models`` and views in the top-level step modules and
``aiidalab_alc.wizards``.

Data input
----------

.. automodule:: aiidalab_alc.data
   :exclude-members: DataStepModel

Workflow configuration
----------------------

.. automodule:: aiidalab_alc.workflow
   :exclude-members: WorkflowCalculationModel

Computational resources
-----------------------

.. automodule:: aiidalab_alc.resources
   :exclude-members: ComputationalResourcesModel

Results
-------

.. automodule:: aiidalab_alc.results
   :exclude-members: ResultsModel

Models
------

.. automodule:: aiidalab_alc.models.data_model

.. automodule:: aiidalab_alc.models.workflow_model

.. automodule:: aiidalab_alc.models.resources_model

.. automodule:: aiidalab_alc.models.results_model

.. automodule:: aiidalab_alc.models.process_model

Wizards
-------

.. automodule:: aiidalab_alc.wizards.structure_step_wizard

.. automodule:: aiidalab_alc.wizards.forceconstant_step_wizard

.. automodule:: aiidalab_alc.wizards.mlip_workflow

.. automodule:: aiidalab_alc.wizards.ins_workflow
