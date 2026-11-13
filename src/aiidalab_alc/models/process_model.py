"""Model describing an AiiDA process."""

from typing import cast

import traitlets as tl
from aiida.common.exceptions import NotExistent
from aiida.orm import NodeLinksManager, ProcessNode, load_node

# bool8 was deprecated in numpy 1.24, but BandsDataViewer still uses it,
# so alias it to bool_ for compatibility.
# if np.__version__ >= "1.24":
#    np.bool8 = bool


class ProcessModel(tl.HasTraits):
    """Model describing an AiiDA process."""

    process_uuid = tl.Unicode(None, allow_none=True)
    process_log = tl.Unicode("", allow_none=True)

    @property
    def process(self) -> ProcessNode | None:
        """Return the process node for the stored uuid."""
        if not self.process_uuid:
            return None
        try:
            return cast(ProcessNode, load_node(self.process_uuid))
        except NotExistent:
            return None

    @property
    def has_process(self) -> bool:
        """Return true if a valid process node is associated with the uuid."""
        return self.process is not None

    @property
    def inputs(self) -> NodeLinksManager | list:
        """Return the inputs for the process."""
        return self.process.inputs if self.has_process else []

    @property
    def outputs(self) -> NodeLinksManager | list:
        """Return the outputs for the process."""
        return self.process.outputs if self.has_process else []
