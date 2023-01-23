# strip latex math wrapping for labels
# (since MathJax isn't yet supported in hover labels, see https://github.com/plotly/plotly.js/issues/559)
# TODO: add this to string utils in pymatgen
from __future__ import annotations

pretty_labels = {
    "$": "",
    "\\mid": "|",
    "\\Gamma": "Γ",
    "\\Sigma": "Σ",
    "GAMMA": "Γ",
    "_1": "₁",
    "_2": "₂",
    "_3": "₃",
    "_4": "₄",
    "_{1}": "₁",
    "_{2}": "₂",
    "_{3}": "₃",
    "_{4}": "₄",
    "^{*}": "*",
}
