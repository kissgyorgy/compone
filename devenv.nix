{ pkgs, lib, config, ... }:
let
  rootDir = config.devenv.root;
in
{
  # https://devenv.sh/basics/
  env = {
    UV_PYTHON_DOWNLOADS = "never";
    UV_PROJECT_ENVIRONMENT = "${rootDir}/.venvs/py3.12";
    PYTHONPATH = lib.concatMapStringsSep ":" (p: "${rootDir}/${p}")
      [ "core" "cli" "frameworks/bootstrap5" "stories" "ssg" ];
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
        python310
        python311
        python313
        uv
      ];
      ignoreCollisions = true;
    })
  ];

  enterShell = ''
    source ${rootDir}/.venvs/py3.12/bin/activate
  '';

  scripts.activate-version.exec = ''
    VERSION=$1
    export VIRTUAL_ENV=${rootDir}/.venvs/py$VERSION
    uv run --active -p python$VERSION -- $SHELL
  '';

  scripts.run-version.exec = ''
    VERSION=$1
    shift
    COMMAND="$@"
    export VIRTUAL_ENV=${rootDir}/.venvs/py$VERSION
    uv run --active -p python$VERSION -- $COMMAND
  '';

  languages.javascript = {
    # for compone-stories
    bun.enable = true;
  };

  # https://devenv.sh/pre-commit-hooks/
  git-hooks.default_stages = [
    "pre-push"
    "manual"
  ];
  git-hooks.hooks = {
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
