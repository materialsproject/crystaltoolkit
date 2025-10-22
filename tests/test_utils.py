from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytest
from dash import Dash, Output
from pymatgen.core import Lattice, Structure

from crystal_toolkit.helpers.utils import hook_up_fig_with_struct_viewer


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create sample data for testing."""
    # Create a simple structure
    struct = Structure(
        lattice=Lattice.cubic(3),
        species=("Fe", "Fe"),
        coords=((0, 0, 0), (0.5, 0.5, 0.5)),
    )

    # Create a DataFrame with some sample data
    return pd.DataFrame(
        {
            "material_id": ["mp-1", "mp-2"],
            "nsites": [2, 4],
            "volume": [10, 20],
            "structure": [struct, struct],
        }
    ).set_index("material_id", drop=False)


@pytest.fixture
def fig(sample_df: pd.DataFrame) -> go.Figure:
    # Create a simple scatter plot
    return px.scatter(
        sample_df, x="nsites", y="volume", hover_name=sample_df.index.name
    )


def test_basic_functionality(fig: go.Figure, sample_df: pd.DataFrame):
    """Test that the function creates a Dash app with the expected components."""
    app = hook_up_fig_with_struct_viewer(fig, sample_df)

    # Check that the app was created
    assert isinstance(app, Dash)

    # Check that the layout contains expected components
    layout = app.layout
    assert layout is not None
    assert "plot" in str(layout)
    assert "structure" in str(layout)
    assert "hover-click-dropdown" in str(layout)


def test_callback_behavior(fig: go.Figure, sample_df: pd.DataFrame):
    """Test that the callback updates the structure and annotations correctly."""
    app = hook_up_fig_with_struct_viewer(fig, sample_df)

    # Create sample hover data
    hover_data = {"points": [{"x": 2, "y": 10, "hovertext": "mp-1"}]}

    # Find the callback that has plot.figure as an output
    callback_key = None
    for key, value in app.callback_map.items():
        output = value.get("output", [])
        outputs = [output] if isinstance(output, Output) else output

        if any(
            isinstance(output, Output)
            and output.component_id == "plot"
            and output.component_property == "figure"
            for output in outputs
        ):
            callback_key = key
            break

    assert callback_key.endswith("struct-title.children...plot.figure..")
    callback = app.callback_map[callback_key]["callback"]

    # Get the input and state definitions
    inputs = app.callback_map[callback_key]["inputs"]
    states = app.callback_map[callback_key]["state"]

    # Create the input arguments in the correct order
    args = []
    for input_def in inputs:
        if input_def["property"] == "hoverData":
            args.append(hover_data)
        elif input_def["property"] == "clickData":
            args.append(None)
        else:
            raise ValueError(f"Unexpected input property: {input_def['property']}")

    # Add state arguments in the correct order
    for state_def in states:
        if state_def["property"] == "value":
            args.append("hover")
        elif state_def["property"] == "figure":
            args.append(fig.to_dict())
        else:
            raise ValueError(f"Unexpected state property: {state_def['property']}")

    # Convert Output objects to dictionaries for outputs_list
    outputs = app.callback_map[callback_key]["output"]
    if isinstance(outputs, Output):
        outputs = [outputs]
    outputs_list = [
        {"id": output.component_id, "property": output.component_property}
        for output in outputs
    ]

    # Call the callback with the arguments in the correct order and outputs_list as a keyword argument
    result = callback(*args, outputs_list=outputs_list)

    # Basic assertion that we got a result
    assert result.startswith('{"multi":true,"response"')


def test_click_mode(fig: go.Figure, sample_df: pd.DataFrame):
    """Test that the callback respects the click mode setting."""
    app = hook_up_fig_with_struct_viewer(fig, sample_df)

    # Create sample hover data
    hover_data = {"points": [{"x": 2, "y": 10, "hovertext": "mp-1"}]}

    # Find the callback that has plot.figure as an output
    callback_key = None
    for key, value in app.callback_map.items():
        output = value.get("output", [])
        outputs = [output] if isinstance(output, Output) else output

        if any(
            isinstance(output, Output)
            and output.component_id == "plot"
            and output.component_property == "figure"
            for output in outputs
        ):
            callback_key = key
            break

    assert callback_key.endswith("struct-title.children...plot.figure..")
    callback = app.callback_map[callback_key]["callback"]

    # Get the input and state definitions
    inputs = app.callback_map[callback_key]["inputs"]
    states = app.callback_map[callback_key]["state"]

    # Create the input arguments in the correct order
    args = []
    for input_def in inputs:
        if input_def["property"] == "hoverData":
            args.append(hover_data)
        elif input_def["property"] == "clickData":
            args.append(None)
        else:
            raise ValueError(f"Unexpected input property: {input_def['property']}")

    # Add state arguments in the correct order
    for state_def in states:
        if state_def["property"] == "value":
            args.append("click")
        elif state_def["property"] == "figure":
            args.append(fig.to_dict())
        else:
            raise ValueError(f"Unexpected state property: {state_def['property']}")

    # Convert Output objects to dictionaries for outputs_list
    outputs = app.callback_map[callback_key]["output"]
    if isinstance(outputs, Output):
        outputs = [outputs]
    outputs_list = [
        {"id": output.component_id, "property": output.component_property}
        for output in outputs
    ]

    # Call the callback with the arguments in the correct order and outputs_list as a keyword argument
    result = callback(*args, outputs_list=outputs_list)

    # Basic assertion that we got a result
    assert result.startswith('{"multi":true,"response"')


def test_custom_highlight(fig: go.Figure, sample_df: pd.DataFrame):
    """Test that custom highlighting function works."""

    def custom_highlight(point):
        return {
            "x": point["x"],
            "y": point["y"],
            "xref": "x",
            "yref": "y",
            "text": f"Custom: {point['hovertext']}",
            "showarrow": True,
        }

    app = hook_up_fig_with_struct_viewer(
        fig, sample_df, highlight_selected=custom_highlight
    )

    # Create sample hover data
    hover_data = {"points": [{"x": 2, "y": 10, "hovertext": "mp-1"}]}

    # Find the callback that has plot.figure as an output
    callback_key = None
    for key, value in app.callback_map.items():
        output = value.get("output", [])
        outputs = [output] if isinstance(output, Output) else output

        if any(
            isinstance(output, Output)
            and output.component_id == "plot"
            and output.component_property == "figure"
            for output in outputs
        ):
            callback_key = key
            break

    assert callback_key.endswith("struct-title.children...plot.figure..")
    callback = app.callback_map[callback_key]["callback"]

    # Get the input and state definitions
    inputs = app.callback_map[callback_key]["inputs"]
    states = app.callback_map[callback_key]["state"]

    # Create the input arguments in the correct order
    args = []
    for input_def in inputs:
        if input_def["property"] == "hoverData":
            args.append(hover_data)
        elif input_def["property"] == "clickData":
            args.append(None)
        else:
            raise ValueError(f"Unexpected input property: {input_def['property']}")

    # Add state arguments in the correct order
    for state_def in states:
        if state_def["property"] == "value":
            args.append("hover")
        elif state_def["property"] == "figure":
            args.append(fig.to_dict())
        else:
            raise ValueError(f"Unexpected state property: {state_def['property']}")

    # Convert Output objects to dictionaries for outputs_list
    outputs = app.callback_map[callback_key]["output"]
    if isinstance(outputs, Output):
        outputs = [outputs]
    outputs_list = [
        {"id": output.component_id, "property": output.component_property}
        for output in outputs
    ]

    # Call the callback with the arguments in the correct order and outputs_list as a keyword argument
    result = callback(*args, outputs_list=outputs_list)

    # Basic assertion that we got a result
    assert result.startswith('{"multi":true,"response"')
