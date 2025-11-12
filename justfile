set windows-shell := ["C:\\Program Files\\Git\\bin\\sh.exe","-c"]
set positional-arguments

@install:
    python -m pip install poetry
    poetry install

@install-dev:
    python -m pip install poetry
    poetry install --with dev

@run *args='':
    poetry run p2p-file-share $@

@lint:
    poetry run mypy .

@check-format:
    poetry run ruff check p2p_file_share tests
    
@format:
    poetry run ruff check --fix p2p_file_share tests

@test:
    poetry run pytest -W ignore
