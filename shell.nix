{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/f480f9d09e4b.tar.gz") {}
}:

pkgs.mkShell {
  packages = [
    pkgs.pre-commit
    pkgs.git
    pkgs.vim
    pkgs.poetry
    pkgs.stdenv
    (pkgs.python3.withPackages(ps: with ps; [seaborn pandas numpy jupyter papermill mkdocs tabulate pytest]))
  ];
  shellHook =
    ''
      poetry install
      export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib";
    '';
}

