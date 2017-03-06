import sys
from cx_Freeze import setup, Executable
from merge_tiles import VERSION

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    "build_exe": {"includes": ['atexit', 'PyQt4.QtWebKit'],
                  "include_files": ['web'],
                  "excludes": ["tkinter", "PyQt4.QtSql", "sqlite3",
                                  "scipy.lib.lapack.flapack",
                                  "PyQt4.QtScript",
                                  "numpy.core._dotblas",
                                  "PyQt5"],
                  "optimize": 2
                  }
}

exe = Executable(
    script="tileparser_gui.py",
    initScript=None,
    base=base,  # None or "Win32GUI"
    targetName="bing.exe",  # this is the name of the executable file
    copyDependentFiles=True,
    compress=True,
    appendScriptToExe=True,
    appendScriptToLibrary=True,
    icon='TileParser.ico'  # if you want to use an icon file, specify the file name here
)

setup(name="Bing_tile_parser",
      version="%s" % VERSION,
      description="Bing tiles parser",
      options=options,
      executables=[exe]
      )
