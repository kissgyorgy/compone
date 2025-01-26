{ pkgs, lib, config, inputs, ... }:
let
  root-dir = config.devenv.root;
in
{
  # https://devenv.sh/basics/

  # https://devenv.sh/packages/
  packages = with pkgs; [
    just
    watchexec
    # needed for lxml
    libxml2
    libxslt
    libz
    (buildEnv {
      name = "python";
      paths = [
        python39
        python310
        python311
        python312
        python313
      ];
      ignoreCollisions = true;
    })
  ];

  scripts.run-python-version.exec = ''
    #!/usr/bin/env bash
    VERSION=$1
    shift
    COMMAND="$@"
    export POETRY_VIRTUALENVS_IN_PROJECT="false"
    export POETRY_VIRTUALENVS_PATH="$DEVENV_ROOT/.venvs"
    export POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON="true"
    poetry -C $DEVENV_ROOT env use $VERSION
    poetry -C $DEVENV_ROOT run -- $COMMAND
  '';

  languages.python = {
    enable = true;
    poetry = {
      enable = true;
      activate.enable = true;
      install.enable = true;
      install.verbosity = "little";
    };
  };
  languages.javascript = {
    # for compone-stories
    bun.enable = true;
  };

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.default_stages = [ "pre-push" "manual" ];
  pre-commit.hooks = {
    ruff = {
      enable = true;
      args = [ "--config" "${root-dir}/pyproject.toml" ];
    };
    ruff-format.enable = true;
    check-added-large-files.enable = true;
    check-json.enable = true;
    check-toml.enable = true;
    check-yaml = {
      enable = true;
      excludes = [ "docs/mkdocs.yml" ];
    };
    trim-trailing-whitespace = {
      enable = true;
      excludes = [ ".*.md$" ];
    };
    end-of-file-fixer.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}
