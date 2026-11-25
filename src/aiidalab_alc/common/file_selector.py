"""Widget for browsing to and selecting a file or directory path."""

import html
import os

import traitlets as tl
from ipywidgets import HTML, Button, HBox, Layout, Select, Text, VBox


class FilenameSelector(VBox, tl.HasTraits):
    """
    A widget for browsing and selecting a file or directory.

    Examples
    --------
    ::

        selector = FilenameSelector(
            extensions=[".cif", ".xyz", ".json"],
        )
        display(selector)

        # Access the selected filename
        print(selector.filename)

        # React to selected path and path type changes
        selector.observe(lambda change: print(change["new"]), names="filename")
        selector.observe(lambda change: print(change["new"]), names="selection_type")
    """

    filename = tl.Unicode("", help="The currently selected filename.")
    selection_type = tl.Unicode(
        "file", help="Whether the selected path is a file or directory."
    )
    directory = tl.Unicode("", help="The directory currently shown in the browser.")

    def __init__(
        self,
        label="Select filename:",
        placeholder="Enter filename...",
        extensions=None,
        default="mace_mp_small.model",
        directory=".",
        **kwargs,
    ):
        """
        Initialise the file selector.

        Parameters
        ----------
        label : str
            Accepted for backward compatibility; not displayed.
        placeholder : str
            Accepted for backward compatibility; not displayed.
        extensions : list of str or None
            If provided (e.g. [".cif", ".xyz"]), restricts the listed files
            to those extensions.
        default : str
            Pre-filled path value.
        directory : str
            Initial directory shown in the file browser.
        """
        self._extensions = extensions
        initial_directory = os.path.abspath(directory)

        self._selected_path = default.strip()

        # ── Status / feedback area ────────────────────────────────────────
        self._status = HTML(value="")

        self._directory_text = Text(
            continuous_update=False,
            value=initial_directory,
            layout=Layout(width="320px"),
            style={"description_width": "0px"},
        )
        # Clickable listing: clicking a directory opens it, clicking a file
        # selects it.
        self._entries = Select(
            options=[],
            rows=10,
            layout=Layout(width="400px"),
            style={"description_width": "0px"},
        )
        self._suppress_entry_events = False
        self._up_btn = Button(
            description="Up",
            icon="level-up",
            layout=Layout(width="70px"),
            tooltip="Show the parent directory",
        )
        self._refresh_btn = Button(
            description="Refresh",
            icon="refresh",
            layout=Layout(width="90px"),
            tooltip="Refresh files and directories",
        )
        self._select_btn = Button(
            description="Select",
            icon="check",
            layout=Layout(width="80px"),
            tooltip="Select the current directory",
        )
        self._clear_btn = Button(
            description="Clear",
            button_style="",
            icon="times",
            layout=Layout(width="80px"),
            tooltip="Clear the filename",
        )
        browser = HBox(
            [self._directory_text, self._up_btn, self._refresh_btn],
            layout=Layout(align_items="center", gap="6px"),
        )
        entry_row = HBox(
            [self._select_btn, self._clear_btn],
            layout=Layout(align_items="center", gap="6px"),
        )

        self._up_btn.on_click(self._on_up)
        self._refresh_btn.on_click(self._on_refresh)
        self._select_btn.on_click(self._on_select_entry)

        self._clear_btn.on_click(self._on_clear)

        # ── Assemble layout ───────────────────────────────────────────────
        self._entries.observe(self._on_entry_click, names="value")
        self._directory_text.observe(
            lambda _change: self._on_refresh(None), names="value"
        )

        super().__init__(
            children=[browser, self._entries, entry_row, self._status],
            layout=Layout(padding="10px", width="auto"),
            **kwargs,
        )

        # Trigger initial sync
        self.directory = initial_directory
        self._refresh_entries()
        self._sync_filename()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _sync_filename(self):
        """Sync the selected path to the public filename trait."""
        self.filename = self._selected_path
        self._update_status(self._selected_path)

    def _update_status(self, filename):
        if not filename:
            self._status.value = (
                "<span style='color:#888; font-size:0.85em;'>"
                "No filename entered.</span>"
            )
        else:
            kind = "Directory" if self.selection_type == "directory" else "File"
            escaped_filename = html.escape(filename)
            self._status.value = (
                f"<span style='color:#2a7; font-size:0.85em;'>✔ {kind}: "
                f"<code>{escaped_filename}</code></span>"
            )

    def _on_clear(self, _btn):
        self._selected_path = ""
        self.selection_type = "file"
        self._sync_filename()

    def _on_refresh(self, _btn):
        candidate = os.path.abspath(
            os.path.expanduser(self._directory_text.value.strip() or ".")
        )
        if not os.path.isdir(candidate):
            self._status.value = (
                "<span style='color:#b33; font-size:0.85em;'>"
                "Directory not found.</span>"
            )
            return
        self.directory = candidate
        self._refresh_entries()

    def _refresh_entries(self):
        self._suppress_entry_events = True
        self._directory_text.value = self.directory
        try:
            entries = []
            allowed_extensions = {item.casefold() for item in self._extensions or []}
            with os.scandir(self.directory) as directory_entries:
                for entry in directory_entries:
                    try:
                        is_directory = entry.is_dir()
                        if is_directory or entry.is_file():
                            extension = os.path.splitext(entry.name)[1].casefold()
                            if (
                                not is_directory
                                and allowed_extensions
                                and extension not in allowed_extensions
                            ):
                                continue
                            prefix = "\U0001f4c1 " if is_directory else "\U0001f4c4 "
                            entries.append((prefix + entry.name, entry.path))
                    except OSError:
                        continue
            entries.sort(
                key=lambda item: (not os.path.isdir(item[1]), item[0].casefold())
            )
            parent = os.path.dirname(self.directory)
            up = [("\u2b06 ..", parent)] if parent != self.directory else []
            self._entries.options = [*up, *entries]
            self._entries.value = None
        except OSError:
            self._entries.options = [("Unable to read this directory", "")]
        finally:
            self._suppress_entry_events = False

    def _on_entry_click(self, change):
        """Open a clicked directory, or select a clicked file."""
        if self._suppress_entry_events:
            return
        selected = change["new"]
        if not selected:
            return
        if os.path.isdir(selected):
            self.directory = os.path.abspath(selected)
            self._refresh_entries()
        else:
            self.selection_type = "file"
            self._selected_path = selected
            self._sync_filename()

    def _on_up(self, _btn):
        parent = os.path.dirname(os.path.abspath(self.directory))
        self.directory = parent
        self._refresh_entries()

    def _on_select_entry(self, _btn):
        """Select the directory currently being shown."""
        self.selection_type = "directory"
        self._selected_path = self.directory
        self._sync_filename()

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
    directory=".",
):
    """
    Return a ready-to-display FilenameSelector widget.

    Parameters
    ----------
    label : str
    placeholder : str
    extensions : list[str] or None
    default : str
    directory : str

    Returns
    -------
    FilenameSelector
    """
    return FilenameSelector(
        label=label,
        placeholder=placeholder,
        extensions=extensions,
        default=default,
        directory=directory,
    )
