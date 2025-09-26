from typing import Callable, Dict, Type

import typer

from p2p_file_share.commands.command import Command

# Global registry mapping command name -> Command subclass (or instance)
NAME_TO_COMMAND: Dict[str, Command] = {}
CODE_TO_COMMAND: Dict[str, Command] = {}
NAME_TO_CODE: Dict[str, str] = {}


COMMAND_CODE_LENGTH = 3  # Fixed length for command codes


def register_command(code: str) -> Callable[..., Type[Command]]:
    """Register a Command subclass."""
    if len(code) != COMMAND_CODE_LENGTH:
        raise ValueError("Command code must be exactly 3 characters long")

    def inner(cmd_cls: Type[Command]) -> Type[Command]:
        """Register a Command subclass.

        Used as a class decorator. The decorated class should set a `code` attribute (string).
        """
        name = cmd_cls.__name__.lower()
        if name in NAME_TO_COMMAND:
            raise KeyError(f"Command '{cmd_cls.__name__}' is already registered")
        instance = cmd_cls()
        NAME_TO_COMMAND[name] = instance
        CODE_TO_COMMAND[code] = instance
        NAME_TO_CODE[name] = code
        return cmd_cls
    return inner


def get_command(name: str="", code: str="") -> Command:
    """Retrieve a registered Command subclass by name or code.

    :param name: The name of the command to retrieve.
    :param code: The code of the command to retrieve.
    """
    if name:
        try:
            return NAME_TO_COMMAND[name]
        except KeyError as exc:
            raise KeyError(f"Unknown command: {name}") from exc
    elif code:
        try:
            return CODE_TO_COMMAND[code]
        except KeyError as exc:
            raise KeyError(f"Unknown command code: {code}") from exc
    raise ValueError("Either name or code must be provided")


def print_commands() -> None:
    """Return the available command names."""
    # Print a nicely formatted list of commands with their code and help text.
    if not NAME_TO_COMMAND:
        typer.echo("No commands registered.")
        return

    # Determine column widths
    entries = []
    for name, cmd_cls in sorted(NAME_TO_COMMAND.items()):
        code = NAME_TO_CODE.get(name, "")
        try:
            help_text = cmd_cls.help()
        except Exception:
            help_text = "(no help available)"
        entries.append((name, code, help_text))

    name_width = max(len(e[0]) for e in entries)
    code_width = max(len(e[1]) for e in entries)

    header = f"{'NAME'.ljust(name_width)}  {'CODE'.ljust(code_width)}  HELP"
    typer.echo(header)
    typer.echo("-" * len(header))
    for name, code, help_text in entries:
        typer.echo(f"{name.ljust(name_width)}  {code.ljust(code_width)}  {help_text}")
