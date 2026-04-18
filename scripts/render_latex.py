"""Render Jinja2 LaTeX templates with data to produce .tex files."""

import json
import os
import re
import sys

from jinja2 import Environment, FileSystemLoader


def escape_latex(value):
    """Escape LaTeX special characters in a string.
    
    Escapes: _, &, %, $, #, {, }, ~, ^, \
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)

    # Escape backslash first, then other special chars
    result = value.replace("\\", "\\textbackslash{}")
    result = result.replace("&", "\\&")
    result = result.replace("%", "\\%")
    result = result.replace("$", "\\$")
    result = result.replace("#", "\\#")
    result = result.replace("{", "\\{")
    result = result.replace("}", "\\}")
    result = result.replace("~", "\\textasciitilde{}")
    result = result.replace("^", "\\textasciicircum{}")
    result = result.replace("_", "\\_")
    return result


def render_template(
    template_name: str,
    data: dict,
    output_path: str,
    templates_dir: str = None,
) -> str:
    """Render a Jinja2 LaTeX template with data and write to output_path.

    Uses <% %> for blocks and {{ }} for variables to avoid conflicts
    with LaTeX curly braces in most contexts.

    Args:
        template_name: Name of the template file (e.g., 'exercise.tex.j2').
        data: Dict of template variables.
        output_path: Path to write the rendered .tex file.
        templates_dir: Path to templates directory. Defaults to ../templates/.

    Returns:
        The output_path where the file was written.
    """
    if templates_dir is None:
        templates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "templates"
        )

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="{{",
        variable_end_string="}}",
        comment_start_string="<#",
        comment_end_string="#>",
    )

    # Register the escape filter
    env.filters["escape_latex"] = escape_latex

    template = env.get_template(template_name)
    rendered = template.render(**data)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python render_latex.py <template> <data.json> <output.tex>")
        sys.exit(1)

    template_name = sys.argv[1]
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        data = json.load(f)
    output_path = sys.argv[3]

    render_template(template_name, data, output_path)
    print(f"Rendered to {output_path}")
