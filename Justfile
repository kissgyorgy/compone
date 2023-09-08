pytest := "python -m pytest --pdb -vv tests/"

check:
    ruff check .

test:
    {{ pytest }}

watchtests:
    watchexec --restart --exts py -- {{ pytest }}
