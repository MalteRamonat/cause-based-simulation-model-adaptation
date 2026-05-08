"""
Utilities for persisting optimized parameter values permanently:
  - update_original_values(): merges new values into the JSON store read by Bayesian_Config
  - write_parameter_to_mo_file(): patches the matching line in the Modelica .mo file
"""

import json
import re
from pathlib import Path

_RESOURCES_DIR = Path(__file__).resolve().parent / "Resources"
_ORIGINAL_VALUES_PATH = _RESOURCES_DIR / "original_parameter_values.json"


def update_original_values(param_updates: dict) -> None:
    """Merge param_updates into original_parameter_values.json.

    The updated file is read by Bayesian_Config on the next import/reload,
    so the next optimization session uses the new values as its baseline.
    """
    with open(_ORIGINAL_VALUES_PATH, encoding="utf-8") as f:
        current = json.load(f)
    current.update(param_updates)
    with open(_ORIGINAL_VALUES_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)


def _split_param(param_name: str) -> tuple:
    """Split 'Component.attribute' into ('Component', 'attribute').

    If the name has no dot, returns ('', param_name).
    """
    parts = param_name.rsplit(".", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])


def _format_value(value: float) -> str:
    """Format a float for Modelica: avoid scientific notation for common ranges."""
    if value == int(value) and abs(value) < 1e9:
        return str(int(value))
    return repr(value)


def write_parameter_to_mo_file(mo_path: Path, param_name: str, value: float) -> bool:
    """Replace the current value of param_name in the Modelica .mo file.

    Strategy: each Modelica component is declared on a single line as
        TypePath ComponentName(attr1 = v1, attr2 = v2, ...) annotation(
    We find the line whose component identifier matches, then substitute
    'attr = <old>' with 'attr = <new>' on that line only.

    Returns True if the substitution was made, False if the parameter was
    not found (caller should warn the user).
    """
    component, attr = _split_param(param_name)
    lines = mo_path.read_text(encoding="utf-8").splitlines(keepends=True)

    # Negative lookbehind ensures we match the component name as a standalone
    # identifier, not as a suffix of another name (e.g. 'Filter' not 'Pipe_Input_Filter').
    component_pattern = re.compile(
        rf'(?<![A-Za-z0-9_]){re.escape(component)}\s*\('
    )
    # Word-boundary match for the attribute avoids hitting substrings
    # (e.g. 'r' must not match inside 'redeclare').
    attr_pattern = re.compile(
        rf'\b({re.escape(attr)}\s*=\s*)([^\s,\)\n]+)'
    )

    new_lines = []
    found = False
    for line in lines:
        if not found and component_pattern.search(line):
            new_line, n = attr_pattern.subn(rf'\g<1>{_format_value(value)}', line, count=1)
            if n > 0:
                line = new_line
                found = True
        new_lines.append(line)

    if found:
        mo_path.write_text("".join(new_lines), encoding="utf-8")
    return found
