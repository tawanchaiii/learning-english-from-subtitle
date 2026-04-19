"""Render Jinja2 templates (Typst or LaTeX) with data to produce output files.

For Typst (.typ.j2) templates: uses {{ }} for variables and <% %> for blocks.
  The escape_typst filter handles Typst-specific escaping ([ ] #).
  No LaTeX escaping is needed since Typst has a simpler markup.

For LaTeX (.tex.j2) templates: uses {{ }} for variables and <% %> for blocks.
  The escape_latex filter handles LaTeX special characters.
"""

import json
import os
import sys

from jinja2 import Environment, FileSystemLoader


def escape_latex(value):
    """Escape LaTeX special characters in a string.

    Escapes: _, &, %, $, #, {, }, ~, ^, \\
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)

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


def escape_typst(value):
    """Escape Typst special characters in a string.

    Escapes: \\ [ ] # _ * (Typst markup characters that need escaping in content).
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)

    result = value.replace("\\", "\\\\")
    result = result.replace("[", "\\[")
    result = result.replace("]", "\\]")
    result = result.replace("#", "\\#")
    result = result.replace("_", "\\_")
    result = result.replace("*", "\\*")
    return result


def render_template(
    template_name: str,
    data: dict,
    output_path: str,
    templates_dir: str = None,
) -> str:
    """Render a Jinja2 template with data and write to output_path.

    Uses <% %> for blocks and {{ }} for variables.
    Automatically selects the appropriate escape filter based on
    whether the template is Typst (.typ.j2) or LaTeX (.tex.j2).

    Args:
        template_name: Name of the template file (e.g., 'exercise.typ.j2').
        data: Dict of template variables.
        output_path: Path to write the rendered file.
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

    env.filters["escape_latex"] = escape_latex
    env.filters["escape_typst"] = escape_typst
    env.filters["escape"] = (
        escape_typst if template_name.endswith(".typ.j2") else escape_latex
    )

    template = env.get_template(template_name)
    rendered = template.render(**data)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python render.py <template> <data.json> <output>")
        sys.exit(1)

    template_name = sys.argv[1]
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        data = json.load(f)
    output_path = sys.argv[3]

    render_template(template_name, data, output_path)
    print(f"Rendered to {output_path}")
