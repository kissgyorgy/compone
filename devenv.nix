{ pkgs, lib, config, inputs, ... }:
let
  root-dir = config.devenv.root;
in
{
  # https://devenv.sh/basics/
  env.JUST_UNSTABLE = "1";

  # https://devenv.sh/packages/
  packages = with pkgs; [
    just
    watchexec
  ];

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
    check-yaml.enable = true;
    trim-trailing-whitespace = {
      enable = true;
      excludes = [ ".*.md$" ];
    };
    end-of-file-fixer.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}
