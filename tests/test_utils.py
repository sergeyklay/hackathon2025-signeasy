"""Module for Utils testing."""

import pytest
from jinja2 import TemplateNotFound

from se.utils import load_prompt, render_template_from_file, strtobool


@pytest.mark.parametrize(
    "value",
    (
        "y",
        "Y",
        "yes",
        "t",
        "True",
        "ON",
        1,
    ),
)
def test_should_return_true(value):
    assert strtobool(value) is True


@pytest.mark.parametrize("value", ("n", "N", "no", "f", "False", "OFF", 0))
def test_should_return_false(value):
    assert strtobool(value) is False


def test_should_raise_value_error():
    with pytest.raises(ValueError):
        strtobool("FOO_BAR")


def test_load_prompt_nonexistent_template():
    with pytest.raises(TemplateNotFound):
        load_prompt("nonexistent_template")


def test_render_template_existing_template(tmp_path):
    templates_dir = tmp_path / "prompts"
    templates_dir.mkdir()
    template_file = templates_dir / "test_template.txt"
    template_file.write_text("Hello, World!")

    result = render_template_from_file(
        template_dir=str(templates_dir), template_name="test_template.txt"
    )

    assert result == "Hello, World!"


def test_render_template_with_context(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    template_file = templates_dir / "greeting.txt"
    template_file.write_text("Welcome, {{ username }}! Today is {{ day }}.")

    result = render_template_from_file(
        template_dir=str(templates_dir),
        template_name="greeting.txt",
        username="Alice",
        day="Monday",
    )

    assert result == "Welcome, Alice! Today is Monday."
