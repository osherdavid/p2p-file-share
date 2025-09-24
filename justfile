set windows-shell := ["C:\\Program Files\\Git\\bin\\sh.exe","-c"]
set positional-arguments

@install:
    python -m pip install --user poetry
    poetry install

@install-dev:
    python -m pip install --user poetry
    poetry install --with dev

@run *args='':
    poetry run p2p-file-share $@

@lint:
    poetry run mypy .

@check-format:
    poetry run ruff check client server
    
@format:
    poetry run ruff check --fix client server