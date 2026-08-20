"""Module for providing functionality to deal with files."""

from io import BytesIO

import traitlets as tl
from aiida.orm import SinglefileData
from ipywidgets import FileUpload, HBox, Text, Layout, Label, Dropdown, HTML, Button


class FileUploadWidget(HBox, tl.HasTraits):
    """A widget for uploading files."""

    file = tl.Instance(SinglefileData, allow_none=True)

    def __init__(self, description: str = "File: ", **kwargs):
        """
        FileUploadWidget constructor.

        Parameters
        ----------
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(**kwargs)
        self.file_dict = None

        self.file_upload = FileUpload(
            accept=" ",
            multiple=False,
            description="Upload",
            layout={"width": "20%"},
        )
        self.file_handle = Text(
            value="",
            placeholder="",
            description=description,
            disabled=True,
            layout={"width": "70%"},
        )
        self.children = [self.file_handle, self.file_upload]

        self.file_upload.observe(self._on_file_upload, names="value")

        return

    @property
    def has_file(self) -> bool:
        """True if a file has been uploaded."""
        return self.file is not None

    def _on_file_upload(self, _):
        """Handle file upload events."""
        value = self.file_upload.value
        file_dict = None
        if value:
            if isinstance(value, dict):
                file_dict = next(iter(value.values()), None)
            elif isinstance(value, (tuple, list)):
                file_dict = value[0] if len(value) else None

        if file_dict is not None:
            self.file_dict = file_dict
            self.file_handle.value = self.file_dict.get("metadata", {}).get(
                "name", self.file_dict.get("name", "")
            )
            self.file = self.get_aiida_file_object()
        else:
            self.file_dict = None
            self.file_handle.value = ""
            self.file = None
        return

    def get_file_contents(self) -> BytesIO | None:
        """Get the contents of the uploaded file as a BytesIO object."""
        if self.file_dict is not None:
            content = self.file_dict.get("content")
            if hasattr(content, "tobytes"):
                content = content.tobytes()
            return BytesIO(content)
        return None

    def filename(self) -> str:
        """Get the name of the uploaded file."""
        if self.file_dict is not None:
            return self.file_dict.get("metadata", {}).get(
                "name", self.file_dict.get("name", "")
            )
        return ""

    def get_aiida_file_object(self):
        """Get the uploaded file as an AiiDA SinglefileData object."""
        filename = self.filename()
        if self.file_dict is not None:
            return SinglefileData(
                file=self.get_file_contents(),
                filename=filename,
                label=filename,
                description=self.file_handle.description,
            )
        return None

    def disable(self, val: bool) -> None:
        """Disable the file upload widget."""
        self.file_upload.disabled = val
        return




class FilenameSelector(HBox, tl.HasTraits):
    """
    A widget for selecting or entering a filename.

    Usage:
        selector = FilenameSelector(
            label="Output filename:",
            placeholder="e.g. my_structure.cif",
            extensions=[".cif", ".xyz", ".json"],
        )
        display(selector)

        # Access the selected filename
        print(selector.filename)

        # React to changes
        selector.observe(lambda change: print(change["new"]), names="filename")
    """

    filename = tl.Unicode("", help="The currently selected filename.")

    def __init__(
        self,
        label="Select filename:",
        placeholder="Enter filename...",
        extensions=None,
        default="mace_mp_small.model",
        **kwargs,
    ):
        """
        Parameters
        ----------
        label : str
            Label shown above the input field.
        placeholder : str
            Placeholder text for the text input.
        extensions : list of str or None
            If provided (e.g. [".cif", ".xyz"]), a dropdown with allowed
            extensions is shown next to the text field so users can pick
            an extension separately from the base name.
        default : str
            Pre-filled filename value.
        """
        self._extensions = extensions

        # ── Header label ──────────────────────────────────────────────────
        self._label = Label(
            value=label,
            style={"font_weight": "bold"},
            layout=Layout(margin="0 0 4px 0"),
        )

        # ── Base-name text input ──────────────────────────────────────────
        self._text = Text(
            value=default,
            placeholder=placeholder,
            layout=Layout(width="320px"),
            style={"description_width": "0px"},
        )

        # ── Optional extension dropdown ───────────────────────────────────
        if extensions:
            self._ext_dropdown = Dropdown(
                options=extensions,
                value=extensions[0],
                layout=Layout(width="100px"),
                style={"description_width": "0px"},
            )
            input_row = HBox(
                [self._text, self._ext_dropdown],
                layout=Layout(align_items="center", gap="6px"),
            )
            self._ext_dropdown.observe(self._on_change, names="value")
        else:
            self._ext_dropdown = None
            input_row = HBox([self._text])

        # ── Status / feedback area ────────────────────────────────────────
        self._status = HTML(value="")

        # ── Clear button ──────────────────────────────────────────────────
        self._clear_btn = Button(
            description="Clear",
            button_style="",
            icon="times",
            layout=Layout(width="80px", height="32px"),
            tooltip="Clear the filename",
        )
        self._clear_btn.on_click(self._on_clear)

        controls_row = HBox(
            [self._clear_btn],
            layout=Layout(margin="4px 0 0 0"),
        )

        # ── Wire up events ────────────────────────────────────────────────
        self._text.observe(self._on_change, names="value")

        # ── Assemble layout ───────────────────────────────────────────────
        super().__init__(
            children=[self._label, input_row, controls_row, self._status],
            layout=Layout(padding="10px", width="auto"),
            **kwargs,
        )

        # Trigger initial sync
        self._sync_filename()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _sync_filename(self):
        """Combine the text field and (optional) extension into self.filename."""
        base = self._text.value.strip()

        if self._ext_dropdown is not None:
            ext = self._ext_dropdown.value
            # Avoid double extension if the user already typed it
            if base.endswith(ext):
                combined = base
            else:
                # Strip any other extension the user may have typed
                import os

                root, _ = os.path.splitext(base)
                combined = (root or base) + ext if base else ""
        else:
            combined = base

        self.filename = combined
        self._update_status(combined)

    def _update_status(self, filename):
        if not filename:
            self._status.value = "<span style='color:#888; font-size:0.85em;'>No filename entered.</span>"
        else:
            self._status.value = (
                f"<span style='color:#2a7; font-size:0.85em;'>✔ Filename: <code>{filename}</code></span>"
            )

    def _on_change(self, change):
        self._sync_filename()

    def _on_clear(self, _btn):
        self._text.value = ""
        if self._ext_dropdown is not None:
            self._ext_dropdown.value = self._ext_dropdown.options[0]

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def value(self):
        """Alias for self.filename (mirrors ipywidgets conventions)."""
        return self.filename

    def reset(self):
        """Clear the widget back to an empty state."""
        self._on_clear(None)


# ── Convenience factory ────────────────────────────────────────────────────────

def create_filename_selector(
    label="Select filename:",
    placeholder="Enter filename...",
    extensions=None,
    default="",
):
    """
    Factory function – returns a ready-to-display FilenameSelector widget.

    Parameters
    ----------
    label : str
    placeholder : str
    extensions : list[str] or None
    default : str

    Returns
    -------
    FilenameSelector
    """
    return FilenameSelector(
        label=label,
        placeholder=placeholder,
        extensions=extensions,
        default=default,
    )

