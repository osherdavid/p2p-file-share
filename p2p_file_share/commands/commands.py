from typing import Callable, Dict, Type, List

from p2p_file_share.commands.command import Command

# Global registry mapping command name -> Command subclass (or instance)
NAME_TO_COMMAND: Dict[str, Type[Command]] = {}
CODE_TO_COMMAND: Dict[str, Type[Command]] = {}
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
        NAME_TO_COMMAND[name] = cmd_cls
        CODE_TO_COMMAND[code] = cmd_cls
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
            return NAME_TO_COMMAND[name]()
        except KeyError as exc:
            raise KeyError(f"Unknown command: {name}") from exc
    elif code:
        try:
            return CODE_TO_COMMAND[code]()
        except KeyError as exc:
            raise KeyError(f"Unknown command code: {code}") from exc
    raise ValueError("Either name or code must be provided")


def list_commands() -> List[str]:
    """Return the available command names."""
    return list(NAME_TO_COMMAND.keys())
