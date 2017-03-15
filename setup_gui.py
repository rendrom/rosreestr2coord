import sys
from cx_Freeze import setup, Executable
from scripts.parser import VERSION

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    "build_exe": {"includes": ['atexit', 'PyQt4.QtWebKit'],
    
                  "include_files": ['gui/dist'],
                  "excludes": ["tkinter", "PyQt4.QtSql", "sqlite3",
                                  "scipy.lib.lapack.flapack",
                                  "PyQt4.QtScript",
                                  "numpy.core._dotblas",
                                  "PyQt5"],
                  "optimize": 2
                  }
}

exe = Executable(
    script="gui.py",
    initScript=None,
    base=base,  # None or "Win32GUI"
    targetName="rosreestr2coord_gui.exe",  # this is the name of the executable file
    copyDependentFiles=True,
    compress=True,
    appendScriptToExe=True,
    appendScriptToLibrary=True,
    icon='TileParser.ico'  # if you want to use an icon file, specify the file name here
)

setup(name="rosreestr2coord_gui",
      version="%s" % VERSION,
      description="Get geometry from rosreestr",
      author='Artemiy Doroshkov',
      author_email='rendrom@gmail.com',
      options=options,
      executables=[exe]
      )
