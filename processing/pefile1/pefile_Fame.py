#!/usr/bin/python
#
# pefile module for FAME (https://github.com/certsocietegenerale/fame)
# 
# Author: Richard Weiss <richard.weiss(at)gmx.de>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#
# Original idea found in:
# https://github.com/xme/fame_modules/blob/master/processing/floss_str/floss_str.py
#
import os

try:
    import pefile
    HAVE_PEFILE = True
except ImportError:
    HAVE_PEFILE = False

from fame.core.module import ProcessingModule
from fame.common.exceptions import ModuleInitializationError
from fame.common.exceptions import ModuleExecutionError

class capa_fame(ProcessingModule):
    name = "PEFile"
    description = "Ero Carrera's pefile for FAME"

    def initialize(self):
        if not HAVE_PEFILE:
            raise ModuleInitializationError(self, "Missing dependency: pefile")

    def each(self, target):
        self.log("info", "PEFile: Begin Processing Sample")
        self.results = {}

        self.log("debug", "Target Sample: " + target)
        try:
            pe = pefile.PE(target)
        except:
            raise ModuleExectionError(self, "Error on Processing Sample " + target)
        imphash = pe.get_imphash()
        self.results = pe.dump_dict()
        self.results['Import Hash'] = imphash

        return True
