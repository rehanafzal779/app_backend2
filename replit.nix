{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.postgresql
    pkgs.pip
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libffi
    ];
    PYTHONBIN = "${pkgs.python311}/bin/python3.11";
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8";
  };
}
