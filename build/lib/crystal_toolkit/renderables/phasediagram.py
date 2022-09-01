from pymatgen.analysis.phase_diagram import PhaseDiagram, PDPlotter


def get_plot(
    self,
    show_unstable=0.2,
    label_stable=True,
    label_unstable=True,
    ordering=None,
    energy_colormap=None,
    process_attributes=False,
    label_uncertainties=False,
):
    """
    Plot a PhaseDiagram.

    :param show_unstable: Whether unstable (above the hull) phases will be
        plotted. If a number > 0 is entered, all phases with
        e_hull < show_unstable (eV/atom) will be shown.
    :param label_stable: Whether to label stable compounds.
    :param label_unstable: Whether to label unstable compounds.
    :param ordering: Ordering of vertices (matplotlib backend only).
    :param energy_colormap: Colormap for coloring energy (matplotlib backend only).
    :param process_attributes: Whether to process the attributes (matplotlib
        backend only).
    :param plt: Existing plt object if plotting multiple phase diagrams (
        matplotlib backend only).
    :param label_uncertainties: Whether to add error bars to the hull (plotly
        backend only). For binaries, this also shades the hull with the
        uncertainty window
    """

    plotter = PDPlotter(self, backend="plotly", show_unstable=show_unstable)

    return plotter.get_plot(
        label_stable=label_stable,
        label_unstable=label_unstable,
        ordering=ordering,
        energy_colormap=energy_colormap,
        process_attributes=process_attributes,
        label_uncertainties=label_uncertainties,
    )


PhaseDiagram.get_plot = get_plot
