pytest := "python -m pytest --pdb -vv tests/"

watchtests:
    watchexec --restart --exts py -- {{ pytest }}

test:
    {{ pytest }}
