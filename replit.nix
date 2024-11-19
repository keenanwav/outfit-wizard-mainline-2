{pkgs}: {
  deps = [
    pkgs.chromium
    pkgs.geckodriver
    pkgs.libGLU
    pkgs.libGL
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.glibcLocales
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.zlib
    pkgs.tk
    pkgs.tcl
    pkgs.openjpeg
    pkgs.libxcrypt
    pkgs.libwebp
    pkgs.libtiff
    pkgs.libjpeg
    pkgs.libimagequant
    pkgs.lcms2
    pkgs.freetype
    pkgs.postgresql
  ];
}
