{ pkgs, config, ... }:
let
  rootDir = config.devenv.root;
in
{
  # https://devenv.sh/basics/
  env = {
    UV_PYTHON_DOWNLOADS = "never";
    UV_PROJECT_ENVIRONMENT = "${rootDir}/.venvs/py3.12";
  };

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
        python312
        python39
        python310
        python311
        python313
        uv
      ];
      ignoreCollisions = true;
    })
  ];

  scripts.run-python-version.exec = ''
    #!/usr/bin/env bash
    VERSION=$1
    shift
    COMMAND="$@"
    export UV_PROJECT_ENVIRONMENT=${rootDir}/.venvs/py$VERSION
    uv run -p python$VERSION -- $COMMAND
  '';

  languages.javascript = {
    # for compone-stories
    bun.enable = true;
  };

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.default_stages = [
    "pre-push"
    "manual"
  ];
  pre-commit.hooks = {
    ruff = {
      enable = true;
      args = [
        "--config"
        "${rootDir}/pyproject.toml"
      ];
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
