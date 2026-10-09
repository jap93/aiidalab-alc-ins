
import html
import os

import traitlets as tl

from ipywidgets import HBox, VBox, Text, Layout, Dropdown, HTML, Button

class FilenameSelector(VBox, tl.HasTraits):
    """
    A widget for browsing and selecting a file or directory.

    Usage:
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
    selection_type = tl.Unicode("file", help="Whether the selected path is a file or directory.")
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
            value=initial_directory,
            layout=Layout(width="320px"),
            style={"description_width": "0px"},
        )
        self._entries = Dropdown(
            options=[("Select a file or directory...", "")],
            layout=Layout(width="320px"),
            style={"description_width": "0px"},
        )
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
        self._open_btn = Button(
            description="Open",
            icon="folder-open",
            layout=Layout(width="80px"),
            tooltip="Open the selected directory",
        )
        self._select_btn = Button(
            description="Select",
            icon="check",
            layout=Layout(width="80px"),
            tooltip="Select the chosen file or directory",
        )
        self._clear_btn = Button(
            description="Clear",
            button_style="",
            icon="times",
            layout=Layout(width="80px"),
            tooltip="Clear the filename",
        )
        browser = HBox(
            [self._directory_text, self._up_btn],
            layout=Layout(align_items="center", gap="6px"),
        )
        entry_row = HBox(
            [self._entries, self._refresh_btn, self._open_btn, self._select_btn, self._clear_btn],
            layout=Layout(align_items="center", gap="6px"),
        )

        self._up_btn.on_click(self._on_up)
        self._refresh_btn.on_click(self._on_refresh)
        self._open_btn.on_click(self._on_open_directory)
        self._select_btn.on_click(self._on_select_entry)

        self._clear_btn.on_click(self._on_clear)

        # ── Assemble layout ───────────────────────────────────────────────
        super().__init__(
            children=[browser, entry_row, self._status],
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
            self._status.value = "<span style='color:#888; font-size:0.85em;'>No filename entered.</span>"
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
        candidate = os.path.abspath(os.path.expanduser(self._directory_text.value.strip() or "."))
        if not os.path.isdir(candidate):
            self._status.value = "<span style='color:#b33; font-size:0.85em;'>Directory not found.</span>"
            return
        self.directory = candidate
        self._refresh_entries()

    def _refresh_entries(self):
        self._directory_text.value = self.directory
        try:
            entries = []
            allowed_extensions = {
                item.casefold() for item in self._extensions or []
            }
            with os.scandir(self.directory) as directory_entries:
                for entry in directory_entries:
                    try:
                        is_directory = entry.is_dir()
                        if is_directory or entry.is_file():
                            extension = os.path.splitext(entry.name)[1].casefold()
                            if not is_directory and allowed_extensions and extension not in allowed_extensions:
                                continue
                            prefix = "[Directory] " if is_directory else "[File] "
                            entries.append((prefix + entry.name, entry.path))
                    except OSError:
                        continue
            entries.sort(key=lambda item: (not os.path.isdir(item[1]), item[0].casefold()))
            self._entries.options = [("Select a file or directory...", ""), *entries]
            self._entries.value = ""
        except OSError:
            self._entries.options = [("Unable to read this directory", "")]

    def _on_up(self, _btn):
        parent = os.path.dirname(os.path.abspath(self.directory))
        self.directory = parent
        self._refresh_entries()

    def _on_open_directory(self, _btn):
        selected = self._entries.value
        if selected and os.path.isdir(selected):
            self.directory = os.path.abspath(selected)
            self._refresh_entries()

    def _on_select_entry(self, _btn):
        selected = self._entries.value
        if not selected:
            return
        is_directory = os.path.isdir(selected)
        self.selection_type = "directory" if is_directory else "file"
        self._selected_path = selected
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
    Factory function – returns a ready-to-display FilenameSelector widget.

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

