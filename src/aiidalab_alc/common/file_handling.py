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

class SelectBinaryFileWidget(HBox, tl.HasTraits):
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




