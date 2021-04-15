#!/usr/bin/python
#
# CAPA module for FAME (https://github.com/certsocietegenerale/fame)
# 
# Author: Richard Weiss <richard.weiss(at)gmx.de>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#
# Original idea found in:
# https://github.com/xme/fame_modules/blob/master/processing/floss_str/floss_str.py
#
# CAPA Project: https://github.com/fireeye/capa
# CAPA Rules: https://github.com/fireeye/capa-rules (Please contribute also new rules)
#

import os
import render
import time

try:
    import vivisect
    HAVE_VIVISECT = True
except ImportError:
    HAVE_VIVISECT = False

try:
    import argparse
    HAVE_ARGPARSE = True
except ImportError:
    HAVE_ARGPARSE = False

try:
    import git
    HAVE_GITPYTHON = True
except ImportError:
    HAVE_GITPYTHON = True

try:
    #from capa.main import main as runner
    from capa.main import get_file_taste
    from capa.main import get_rules
    from capa.rules import RuleSet
    from capa.main import get_extractor
    from capa.main import collect_metadata
    from capa.main import find_capabilities
    HAVE_CAPA = True
except ImportError:
    HAVE_CAPA = False

from fame.core.module import ProcessingModule
from fame.common.exceptions import ModuleInitializationError
from fame.common.exceptions import ModuleExecutionError

class capa_fame(ProcessingModule):
    name = "capa-fame"
    description = "FireEye CAPA Port to FAME"

    config = [
        {
            'name': 'rule_path',
            'type': 'str',
            'description': 'Path to FireEye CAPA Rules'
        },
        {
            'name': 'filetype',
            'type': 'str',
            'default': 'auto',
            'description': 'Type of sample: auto (default), pe, sc32, sc64'
        },
        {
            'name': 'updateall',
            'type': 'bool',
            'default': False,
            'description': 'Update CAPA and CAPA Rules repository'
        },
    ]

    def updateCapaRules(self):
        try:
            caparepo=self.rule_path.rsplit(os.path.sep,1)[0]
            git.Repo(caparepo).remotes.origin.pull()
            git.Repo(caparepo).submodules['rules'].update(to_latest_revision=True)
        except:
            self.log("error", "No Repository Update")
            

    def getCommitHash(self):
        try:
            repo = git.Repo(self.rule_path)
            sha = repo.head.commit.hexsha
        except:
            sha = "Not Git manageded Rule Repository"
        return sha

    def getCommitDate(self):
        try:
            repo = git.Repo(self.rule_path)
            date = time.strftime("%a, %d %b %Y %H:%M", time.gmtime(repo.head.commit.committed_date))
        except:
            date = "Not Git manageded Rule Repository"
        return date

    def initialize(self):
        if not HAVE_CAPA:
            raise ModuleInitializationError(self, "Missing dependency: capa")
        if not HAVE_VIVISECT:
            raise ModuleInitializationError(self, "Missing dependency: vivisect")
        if not HAVE_ARGPARSE:
            raise ModuleInitializationError(self, "Missing dependency: argparse")
        if not HAVE_GITPYTHON:
            raise ModuleInitializationError(self, "Missing dependency: gitpython")

    def each(self, target):
        if self.updateall:
            self.updateCapaRules()

        self.log("info", "Begin Processing Sample")
        self.results = {}

	generic = []
	generic.append(("Rule Path", self.rule_path))
        generic.append(("Commit Date", self.getCommitDate()))
	generic.append(("GitCommit", self.getCommitHash()))
	generic.append(("Filetype", self.filetype))

        request = []
        request.append('-r')
        request.append(self.rule_path)
        request.append('-f')
        request.append(self.filetype)
        request.append(target)

        try:
            taste = get_file_taste(target)
        except:
            raise ModuleExecutionError(self, "Target Sample Error")

        try:
            rules = get_rules(self.rule_path)
        except:
            raise ModuleExecutionError(self, "Rule Path Error")
        rules = RuleSet(rules)

        extractor = get_extractor(target, self.filetype)
        meta = collect_metadata(request, target, self.rule_path, self.filetype, extractor)
        capabilities, counts = find_capabilities(rules, extractor)
        meta['analysis'].update(counts)

        self.log("info", "Begin Process Analysis Results")
        self.results = render.render_fame(meta, rules, capabilities)
        self.results['generic'] = generic

	return True
