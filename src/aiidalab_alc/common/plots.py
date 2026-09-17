"""Widgets used for interactively plotting data."""

from collections.abc import Sequence

import numpy
import plotly.graph_objects as go
from ipywidgets import VBox


class PlotWidget(VBox):
    """Interactive line plot for one or more data series based on plotly.

    Wraps a :class:`plotly.graph_objects.FigureWidget` — itself an ipywidget —
    so the plot integrates natively with an AiiDAlab (ipywidgets) UI. Each data
    series is plotted against a common set of x values (a shared index by
    default), giving the user an interactive figure with zoom, pan and hover
    support.
    """

    def __init__(
        self,
        data_series: numpy.ndarray | Sequence[numpy.ndarray],
        x_values: Sequence[float] | numpy.ndarray | None = None,
        y_label: str = "",
        x_label: str = "Index",
        series_labels: Sequence[str] | None = None,
        title: str = "",
        **kwargs,
    ):
        """PlotWidget Constructor.

        Parameters
        ----------
        data_series : numpy.ndarray | Sequence[numpy.ndarray]
            The y values to plot. Either a single 1D numpy array for a single
            series, or a list of 1D numpy arrays, one per series.
        x_values : Sequence[float] | numpy.ndarray | None, optional
            Shared x values for every series. When ``None`` (default) each
            series is plotted against its own integer index.
        y_label : str, optional
            Label for the y axis.
        x_label : str, optional
            Label for the x axis. Defaults to ``"Index"``.
        series_labels : Sequence[str] | None, optional
            Legend labels for each series. When ``None`` (default) series are
            labelled ``"Series 1"``, ``"Series 2"`` and so on.
        title : str, optional
            Title displayed above the plot.
        """
        super().__init__(**kwargs)

        # Accept either a single array (one series) or a collection of arrays.
        if isinstance(data_series, numpy.ndarray) and data_series.ndim == 1:
            data_series = [data_series]
        # Normalise the data series to a list of 1D numpy arrays.
        self.data_series = [numpy.asarray(series).ravel() for series in data_series]

        if series_labels is None:
            series_labels = [f"Series {i + 1}" for i in range(len(self.data_series))]
        elif len(series_labels) != len(self.data_series):
            raise ValueError(
                "The number of series labels must match the number of data series."
            )
        self.series_labels = list(series_labels)

        self.x_values = None if x_values is None else numpy.asarray(x_values).ravel()
        self.y_label = y_label
        self.x_label = x_label
        self.title = title

        self.figure = go.FigureWidget()
        self._render()

        self.children = [self.figure]
        return

    def _series_x(self, series: numpy.ndarray) -> numpy.ndarray:
        """Return the x values used to plot a single series."""
        if self.x_values is None:
            return numpy.arange(series.shape[0])
        if self.x_values.shape[0] != series.shape[0]:
            raise ValueError(
                "The number of x values must match the length of each data series."
            )
        return self.x_values

    def _render(self) -> None:
        """(Re)build the plotly figure from the current data series."""
        with self.figure.batch_update():
            self.figure.data = []
            for series, label in zip(self.data_series, self.series_labels, strict=True):
                self.figure.add_trace(
                    go.Scatter(
                        x=self._series_x(series),
                        y=series,
                        mode="lines+markers",
                        name=label,
                    )
                )
            self.figure.update_layout(
                title=self.title,
                xaxis_title=self.x_label,
                yaxis_title=self.y_label,
                template="plotly_white",
                showlegend=len(self.data_series) > 1,
                margin={"l": 60, "r": 30, "t": 40 if self.title else 20, "b": 50},
            )
        return
