import pytest

from p2p_file_share.commands import commands
from p2p_file_share.commands.command import Command


class _BaseTestCommand(Command):
    """Minimal command implementation for registry tests."""

    def execute_server(self, conn, addr, *args, **kwargs):
        return (conn, addr, args, kwargs)

    def execute_client(self, conn, *args, **kwargs):
        return (conn, args, kwargs)


def test_register_command_populates_all_registries() -> None:
    """Test command registry globality."""
    @commands.register_command("TST")
    class SampleCommand(_BaseTestCommand):
        """Dummy command used solely for registry validation."""

    key = SampleCommand.__name__.lower()

    assert key in commands.NAME_TO_COMMAND
    assert commands.NAME_TO_COMMAND[key] is commands.CODE_TO_COMMAND["TST"]
    assert commands.NAME_TO_CODE[key] == "TST"


def test_get_command_returns_same_instance_for_name_and_code() -> None:
    """Checks both dicts."""
    @commands.register_command("ABC")
    class AnotherCommand(_BaseTestCommand):
        pass

    instance_by_name = commands.get_command(name="anothercommand")
    instance_by_code = commands.get_command(code="ABC")
    assert instance_by_name is instance_by_code
    assert isinstance(instance_by_name, AnotherCommand)


def test_register_command_rejects_invalid_code_length() -> None:
    """Checks wrong command codes."""
    with pytest.raises(ValueError):
        @commands.register_command("LONG")
        class InvalidCode(_BaseTestCommand):
            pass


def test_get_command_requires_selector() -> None:
    """Checks no command."""
    with pytest.raises(ValueError):
        commands.get_command()
