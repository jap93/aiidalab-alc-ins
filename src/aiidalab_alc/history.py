"""Define the ALC INS calculation history page."""

from datetime import datetime
from html import escape

import ipywidgets as ipw
import traitlets as tl
from aiida.orm import ProcessNode, QueryBuilder
from IPython.display import display

from aiidalab_alc.common.navigation import QuickAccessButtons


class HistoryApp:
    """The calculation history page's main app."""

    def __init__(self):
        """Create and display the history page."""
        self.model = HistoryModel()
        self.view = HistoryAppView(self.model)
        display(self.view)


class HistoryModel(tl.HasTraits):
    """Model for the selected AiiDA process."""

    process_uuid = tl.Unicode(default_value="", allow_none=False)


class HistoryAppView(ipw.VBox):
    """Search and inspect processes created by the ALC INS app."""

    def __init__(self, model: HistoryModel, **kwargs):
        """Build the history page and its process detail view."""
        self.model = model

        logo = ipw.HTML(
            '<div class="app-container logo" style="width: 300px;">'
            '<img src="./images/alc.svg" alt="ALC AiiDAlab App Logo" />'
            "</div>",
            layout={"margin": "auto"},
        )
        header = ipw.VBox(
            children=[logo, QuickAccessButtons()],
            layout={"margin": "auto"},
        )
        title = ipw.HTML("<h2>ALC Calculation History</h2>")

        self.workflow_filter = ipw.Dropdown(
            options=[("All ALC workflows", "all"), ("INS", "ins"), ("MLIP", "mlip")],
            value="all",
            description="Workflow",
            style={"description_width": "initial"},
            layout={"width": "220px"},
        )
        self.text_filter = ipw.Text(
            placeholder="Label, description, or process type",
            description="Filter",
            style={"description_width": "initial"},
            layout={"flex": "1 1 320px"},
        )
        self.search_button = ipw.Button(
            description="Search",
            icon="search",
            button_style="primary",
            tooltip="Search stored ALC processes",
        )
        self.search_button.on_click(self._search)
        self.text_filter.on_submit(self._search)
        filters = ipw.HBox(
            [self.workflow_filter, self.text_filter, self.search_button],
            layout={"align_items": "center", "flex_flow": "row wrap"},
        )

        self.status = ipw.HTML()
        self.process_select = ipw.Dropdown(
            options=[("Choose a process", "")],
            value="",
            description="Process",
            style={"description_width": "initial"},
            layout={"width": "100%"},
        )
        self.process_select.observe(self._show_process, names="value")
        self.details = ipw.HTML(
            "<p>Select a process to inspect its state, inputs, and outputs.</p>"
        )

        footer = ipw.HTML(
            f"<footer>Copyright (c) {datetime.now().year} Ada Lovelace Centre (STFC)</footer>",
            layout={"margin": "2em 0 0 auto"},
        )
        super().__init__(
            children=[
                header,
                title,
                filters,
                self.status,
                self.process_select,
                self.details,
                footer,
            ],
            **kwargs,
        )

        self._search()

    def _search(self, _=None) -> None:
        """Find recent ALC INS and MLIP process nodes in the active profile."""
        filters = {
            "or": [
                {"process_type": {"like": "%aiida_pythonjob_ins%"}},
                {"process_type": {"like": "%aiida_workgraph%"}},
                {"label": {"like": "%GeomOptGraph%"}},
            ]
        }
        query = QueryBuilder().append(
            ProcessNode,
            filters=filters,
            tag="process",
        )
        query.order_by({"process": {"ctime": "desc"}})
        query.limit(200)

        try:
            nodes = [row[0] for row in query.all()]
        except Exception as error:
            self.process_select.options = [("Choose a process", "")]
            self.process_select.value = ""
            self.status.value = (
                "<p style='color:#9b2c2c'>Could not query the active AiiDA profile: "
                f"{escape(str(error))}</p>"
            )
            return

        workflow = self.workflow_filter.value
        needle = self.text_filter.value.strip().casefold()
        matches = [
            node
            for node in nodes
            if self._matches_workflow(node, workflow)
            and (
                not needle
                or needle
                in " ".join(
                    [
                        str(getattr(node, "label", "")),
                        str(getattr(node, "description", "")),
                        str(getattr(node, "process_type", "")),
                        str(node.pk),
                        node.uuid,
                    ]
                ).casefold()
            )
        ]

        options = [("Choose a process", "")]
        options.extend((self._process_label(node), node.uuid) for node in matches)
        self.process_select.options = options
        self.process_select.value = ""
        self.status.value = (
            f"<p>{len(matches)} process(es) found; showing up to 200 recent ALC runs.</p>"
        )
        self.details.value = "<p>Select a process to inspect its state, inputs, and outputs.</p>"

    @staticmethod
    def _matches_workflow(node: ProcessNode, workflow: str) -> bool:
        """Return whether a process belongs to the chosen ALC workflow family."""
        process_type = str(getattr(node, "process_type", "") or "").casefold()
        label = str(getattr(node, "label", "") or "").casefold()
        if workflow == "ins":
            return "aiida_pythonjob_ins" in process_type
        if workflow == "mlip":
            return "aiida_workgraph" in process_type or "geomoptgraph" in label
        return True

    @staticmethod
    def _process_label(node: ProcessNode) -> str:
        """Format a process row for the selector."""
        process_type = str(getattr(node, "process_type", "") or "")
        process_name = process_type.rsplit(".", 1)[-1] or type(node).__name__
        state = getattr(node, "process_state", None)
        state = getattr(state, "value", state) or "created"
        timestamp = node.ctime.strftime("%Y-%m-%d %H:%M")
        label = getattr(node, "label", "") or getattr(node, "description", "")
        return f"{timestamp} | PK {node.pk} | {state} | {process_name} | {label}"[:240]

    def _show_process(self, change) -> None:
        """Render metadata and linked input/output nodes for the selection."""
        process_uuid = change["new"]
        self.model.process_uuid = process_uuid
        if not process_uuid:
            return

        try:
            node = QueryBuilder().append(
                ProcessNode,
                filters={"uuid": {"==": process_uuid}},
            ).first()[0]
        except Exception as error:
            self.details.value = f"<p style='color:#9b2c2c'>{escape(str(error))}</p>"
            return

        process_type = escape(str(getattr(node, "process_type", "") or "Unknown"))
        state = getattr(node, "process_state", None)
        state = escape(str(getattr(state, "value", state) or "Created"))
        exit_status = getattr(node, "exit_status", None)
        description = escape(getattr(node, "description", "") or "")
        self.details.value = (
            "<h3>Process details</h3>"
            "<table><tbody>"
            f"<tr><th>PK</th><td>{node.pk}</td></tr>"
            f"<tr><th>UUID</th><td><code>{escape(node.uuid)}</code></td></tr>"
            f"<tr><th>Type</th><td><code>{process_type}</code></td></tr>"
            f"<tr><th>State</th><td>{state}</td></tr>"
            f"<tr><th>Exit status</th><td>{escape(str(exit_status if exit_status is not None else 'Not finished'))}</td></tr>"
            f"<tr><th>Created</th><td>{node.ctime.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>"
            f"<tr><th>Description</th><td>{description or 'None'}</td></tr>"
            "</tbody></table>"
            f"<h4>Inputs</h4>{self._links_list(node.inputs)}"
            f"<h4>Outputs</h4>{self._links_list(node.outputs)}"
        )

    @staticmethod
    def _links_list(links) -> str:
        """Format direct provenance links as a compact list."""
        items = []
        for label in links:
            linked_node = links[label]
            node_type = type(linked_node).__name__
            node_label = getattr(linked_node, "label", "") or ""
            items.append(
                "<li>"
                f"<code>{escape(str(label))}</code>: "
                f"{escape(node_type)} (PK {linked_node.pk})"
                f"{f' | {escape(node_label)}' if node_label else ''}"
                "</li>"
            )
            if len(items) == 12:
                break
        if not items:
            return "<p>None</p>"
        remaining = len(links) - len(items)
        more = f"<li>...and {remaining} more</li>" if remaining > 0 else ""
        return f"<ul>{''.join(items)}{more}</ul>"
