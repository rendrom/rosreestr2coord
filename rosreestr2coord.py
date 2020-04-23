#!/usr/bin/env python
# coding: utf-8
import warnings
from rosreestr2coord.console import console

if __name__ == "__main__":

    warnings.warn(
        "Command `python rosreestr2coord.py` is deprecated, use `python -m rosreestr2coord`",
        DeprecationWarning
    )
    console()
