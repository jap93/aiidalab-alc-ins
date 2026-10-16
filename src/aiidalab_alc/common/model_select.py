"""Widget for selecting MLIP model."""

from pathlib import Path
from typing import Generic, TypeVar

import ipywidgets as ipw
from aiida.orm import Node, QueryBuilder, SinglefileData

from alc_aiidalab_widgets.utils import tab_from_dict
from alc_aiidalab_widgets.widgets import AiiDADatabaseQueryWidget, FileUploadWidget
from alc_aiidalab_widgets.widgets.parameters import ParamEntry, ParametersBlock

NT = TypeVar("NT", bound=Node)


class ModelError(Exception):
    """Error raised while processing model."""


class ModelSelect(ipw.VBox, Generic[NT]):
    """Widget for selecting MLIP model."""

    def __init__(
        self,
        *,
        model_cls: type[NT] | None = None,
        logspace: ipw.Output | None = None,
        **kwargs,
    ) -> None:

        if logspace is not None:
            self.logspace = logspace
        else:
            self.logspace = ipw.Output()  # Dummy output just dumps nowhere.
        self.model_cls = model_cls
        tabs = {}

        # Arch

        self.arch = ipw.Dropdown(
            options=(
                "mace",
                "mace_mp",
                "mace_off",
                "chgnet",
                "sevennet",
                "nequip",
                "dpa3",
                "orb",
                "mattersim",
                "grace",
                "upet",
                "fairchem",
                "mace_omol",
            ),
            description="Arch:",
            layout=ipw.Layout(width="80%"),
        )
        self.extra_kwargs = ParamEntry(
            # tooltip="Calc kwargs provided as `key=value`", layout={"width": "60%"}
        )

        # Remote Model
        self.model_from_uri = ipw.Text(
            value="",
            description="Model:",
            placeholder="file:///Path/To/Model",
            layout=ipw.Layout(width="80%"),
        )
        uri_vbox = ipw.VBox(
            [self.model_from_uri, self.arch, self.extra_kwargs],
            layout={"width": "100%"},
        )
        parameters_block = ParametersBlock(
            "",
            {
                "model": self.model_from_uri,
                "arch": self.arch,
                "calc_kwargs": self.extra_kwargs,
            },
            {
                "mace_mp_small": {
                    "model": "https://github.com/stfc/janus-core/raw/main/tests/models/mace_mp_small.model",
                    "arch": "mace_mp",
                    "calc_kwargs": {
                        "damping": "bj",
                        "dispersion_xc": "pbe",
                        "dispersion_cutoff": 21,
                    },
                },
                "mace_omol_xl": {
                    "model": "https://github.com/ACEsuit/mace-foundations/releases/download/mace_omol_0/MACE-omol-0-extra-large-1024.model",
                    "arch": "mace_omol",
                    "calc_kwargs": {"default_dtype": "float64"},
                },
                "mace_off_m": {
                    "model": "https://github.com/ACEsuit/mace-off/blob/main/mace_off24/MACE-OFF24_medium.model",
                    "arch": "mace_off",
                    "calc_kwargs": {"default_dtype": "float64"},
                },
                "mace_polar_m": {
                    "model": "https://github.com/ACEsuit/mace-foundations/releases/download/mace_polar_1/MACE-POLAR-1-M.model",
                    "arch": "mace_polar",
                    "calc_kwargs": {"default_dtype": "float64"},
                },
                "chgnet-0.3.0": {
                    "model": "https://github.com/CederGroupHub/chgnet/raw/refs/heads/main/chgnet/pretrained/0.3.0/chgnet_0.3.0_e29f68s314m37.pth.tar",
                    "arch": "chgnet",
                    "calc_kwargs": {},
                },
                "sevennet-Jul2024": {
                    "model": "https://github.com/MDIL-SNU/SevenNet/raw/refs/heads/main/sevenn/pretrained_potentials/SevenNet_0__11Jul2024/checkpoint_sevennet_0.pth",
                    "arch": "sevennet",
                    "calc_kwargs": {"file_type": "checkpoint", "sevennet_config": None},
                },
                "nequip-medium": {
                    "model": "https://zenodo.org/api/records/18775904/files/NequIP-OAM-M-0.1.nequip.zip/content",
                    "arch": "nequip",
                    "calc_kwargs": {},
                },
                "DPA-3-3-1M": {
                    "model": "https://huggingface.co/deepmodelingcommunity/DPA-3.3-1M/resolve/main/DPA-3.3-1M.pt?download=true",
                    "arch": "deepmd",
                    "calc_kwargs": {},
                },
                "orb3-direct-omol": {
                    "model": "https://orbitalmaterials-public-models.s3.us-west-1.amazonaws.com/forcefields/orb-v3-direct-omol-20250820.ckpt",
                    "arch": "orb",
                    "calc_kwargs": {"atoms_adapter": None},
                },
                "mattersim-v1-1M": {
                    "model": "https://github.com/microsoft/mattersim/raw/refs/heads/main/pretrained_models/mattersim-v1.0.0-1M.pth",
                    "arch": "mattersim",
                    "calc_kwargs": {},
                },
                "grace-2L-omat": {
                    "model": "https://huggingface.co/AMS-ICAMS-RUB/grace-foundation-models/resolve/main/models/GRACE-2L-OMAT-model.tar.gz?download=true",
                    "arch": "grace",
                    "calc_kwargs": {},
                },
                "upet-mad-s-1.6": {
                    "model": "https://huggingface.co/lab-cosmo/upet/resolve/main/models/pet-mad-s-v1.6.0.ckpt?download=true",
                    "arch": "upet",
                    "calc_kwargs": {},
                },
            },
        )
        uri_vbox = ipw.HBox([uri_vbox, parameters_block])
        tabs["From URI"] = uri_vbox

        # Local Model
        self.model_from_local = FileUploadWidget()
        local_vbox = ipw.VBox(
            [self.model_from_local, self.arch, self.extra_kwargs],
            layout={"width": "100%"},
        )
        tabs["From Local File"] = local_vbox

        # AiiDA Model
        if self.model_cls:
            self.model_from_node = AiiDADatabaseQueryWidget(
                title="AiiDA Database",
                query=[self.model_cls],
            )
            self.refresh_models_button = ipw.Button(
                description="Refresh",
                button_style="info",
                tooltip="Refresh the list of available models",
                icon="refresh",
                layout={"width": "20%"},
            )
            self.refresh_models_button.on_click(self.update_models)
            self.model_node_box = ipw.HBox(
                [self.model_from_node, self.refresh_models_button],
                layout={"width": "100%"},
            )
            node_vbox = ipw.VBox(
                [self.model_node_box, self.arch, self.extra_kwargs],
                layout={"width": "100%"},
            )
            tabs["AiiDA Database"] = node_vbox

        self.model_type = tab_from_dict(ipw.Tab, tabs)
        super().__init__([self.model_type], **kwargs)

    def update_models(self, _: ipw.Button | None = None) -> None:
        """Update the list of available models."""
        if not self.model_cls:
            return
        qb = QueryBuilder()
        qb.append(self.model_cls, project=["label", "id"])

        models = qb.all()
        model_labels = [(f"{label or repr(label)}:{idx}", idx) for label, idx in models]
        self.model_from_node.options = model_labels

        if model_labels:
            self.model_from_node.value = model_labels[0]

    @property
    def calc_kwargs(self) -> dict[str, str]:
        """Get calc kwargs as dict."""
        return self.extra_kwargs.as_dict()


try:
    import aiida_mlip
except ImportError:
    aiida_mlip = None

if aiida_mlip is not None:
    from aiida_mlip.data.model import ModelData

    class AiiDAMlipModelSelect(ModelSelect[ModelData]):
        """Model selector for aiida-mlip."""

        def __init__(self, logspace: ipw.Output | None = None) -> None:
            super().__init__(model_cls=ModelData, logspace=logspace)

        def _load_from_uri(self, model_str: str, arch: str) -> NT:
            if model_str.startswith(("http", "ftp", "sftp")):
                model_uri = model_str
                self.logspace.append_stdout("Loading model from web...")
            else:
                model_pth = Path(model_str).absolute()
                self.logspace.append_stdout("Loading model from file...")

                if not model_pth.is_file():
                    raise ModelError(f"File ({model_str}) not found.")

                model_uri = model_pth.as_uri()

            try:
                mdl = self.model_cls.from_uri(model_uri, architecture=arch)
            except Exception as err:
                raise ModelError(f"Unable to load model from {model_uri}.") from err

            mdl.label = f"{arch}:{model_uri}"
            return mdl

        def _load_from_node(self, node: NT, arch: str) -> NT:
            return node

        def _load_from_local(self, node: SinglefileData, arch: str) -> NT:
            with node.open(None, "rb") as file:
                return self.model_cls(file, architecture=arch)

        def _try_load_model(self) -> tuple[str, NT]:

            arch = self.arch.value
            typ = self.model_type.get_title(self.model_type.selected_index)

            match typ:
                case "From URI":
                    mdl = self._load_from_uri(self.model_from_uri.value, arch)
                case "AiiDA Database":
                    mdl = self._load_from_node(self.model_from_node.data_object, arch)
                case "From Local File":
                    mdl = self._load_from_local(
                        self.model_from_local.get_aiida_file_object(), arch
                    )

            return arch, mdl
