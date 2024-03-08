pytest := "python -m pytest --pdb -vv tests/"

mod stories

check:
    ruff check .

test:
    {{ pytest }}

watchtests:
    watchexec --restart --exts py -- {{ pytest }}
