"""A module with utility functions."""

import logging
import platform
import re
import subprocess

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


def strtobool(value: str) -> bool:
    """Convert a string representation to a boolean value.

    Args:
        value (str): The string to convert. Case-insensitive.
            Valid true values: 'y', 'yes', 't', 'true', 'on', '1'
            Valid false values: 'n', 'no', 'f', 'false', 'off', '0'

    Returns:
        bool: The boolean value.

    Raises:
        ValueError: If the input string is not a valid boolean representation.
    """
    bool_map = {
        # True
        "y": True,
        "yes": True,
        "t": True,
        "true": True,
        "on": True,
        "1": True,
        # False
        "n": False,
        "no": False,
        "f": False,
        "false": False,
        "off": False,
        "0": False,
    }

    try:
        return bool_map[str(value).lower()]
    except KeyError as exc:
        raise ValueError(f""""{value}" is not a valid bool value""") from exc


def clean_json_string(string: str) -> str:
    """Clean a JSON string by removing markdown code block markers.

    Removes markdown-style JSON code block markers from a string.

    Handles multi-line strings containing JSON content that may be wrapped in
    markdown code blocks (```json). Preserves the actual JSON content while
    removing the markers.

    Args:
        string (str): Input string containing JSON with potential markdown code blocks

    Returns:
        str: Cleaned JSON string with code block markers removed and whitespace trimmed
    """
    # First remove any leading/trailing whitespace
    string = string.strip()

    # Check if the string starts and ends with markdown json code blocks
    if string.startswith("```json") and string.endswith("```"):
        # Remove the starting ```json marker and any whitespace after it
        string = re.sub(r"^```json\s*", "", string)
        # Remove the ending ``` marker and any whitespace before it
        string = re.sub(r"\s*```$", "", string)

    return string.strip()


def is_tool_available(tool_name: str) -> bool:
    """Check if a command-line tool is available in the system PATH.

    Uses platform-specific commands ('where' on Windows, 'which' on Unix-like systems)
    to determine if the specified tool is accessible from the command line.

    Args:
        tool_name (str): Name of the command-line tool to check for

    Returns:
        bool: True if the tool is available in PATH, False otherwise
    """
    try:
        cmd = ["where"] if platform.system() == "Windows" else ["which"]
        cmd.append(tool_name)
        return (
            subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ).returncode
            == 0
        )
    except FileNotFoundError:
        return False


def load_prompt(prompt_name: str, **context) -> str:
    """Load and return a prompt template from the prompts directory.

    Args:
        prompt_name (str): Name of the prompt template file (without extension)
        **context: Variables to be interpolated into the prompt template

    Returns:
        str: The rendered prompt with context variables interpolated

    Note:
        Prompt templates should be stored as .txt files in the prompts directory.
        The template will be rendered using the Jinja2 templating engine.
    """
    return render_template_from_file(
        template_dir="prompts", template_name=f"{prompt_name}.txt", **context
    )


def render_template_from_file(template_dir: str, template_name: str, **context) -> str:
    """Render a template file using Jinja2 templating engine.

    Args:
        template_dir (str): Directory path containing the template file
        template_name (str): Name of the template file to render
        **context: Keyword arguments containing variables to inject into template

    Returns:
        str: The rendered template string with context variables interpolated
    """
    # Create a Jinja environment with the specified template directory
    env = Environment(loader=FileSystemLoader(template_dir))

    # Load the template
    template = env.get_template(template_name)

    # Render the template with the given context
    return template.render(**context)
