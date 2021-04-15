import os
import subprocess
from fame.core.module import ProcessingModule
from fame.common.exceptions import ModuleInitializationError
from distutils.spawn import find_executable


try:
    import pcodedmp
    HAVE_PCODEDMP = True
except ImportError:
    HAVE_PCODEDMP = False

if find_executable("sigtool") is not None:
    HAVE_SIGTOOL = True
else:
    HAVE_SIGTOOL = False


class VbaStomp(ProcessingModule):
    name = "vba_stomp"
    description = "Detects VBA stomping and similar anomalies in documents with VBA code."
    acts_on = ["word", "excel"]

    config = [
        {
            'name': 'pcodedmp_dir',
            'type': 'str',
            'description': 'pcodedmp.py folder path.'
        },
        {
            'name': 'vba_seismograph_path',
            'type': 'str',
            'description': 'vba_seismograph.py file path.'
        },
    ]

    def initialize(self):
        if not HAVE_PCODEDMP:
            raise ModuleInitializationError(self, "Missing dependency: pcodedmp")

        if not HAVE_SIGTOOL:
            raise ModuleInitializationError(self, "Missing dependency: sigtool")

    def each(self, target):

        self.results = {
            'warning': False,
            'output': u''
        }

        scan_proc = subprocess.Popen(
            ["python", self.vba_seismograph_path, target],
            stdout=subprocess.PIPE,
            env=dict(os.environ, PCODEDMP_DIR=self.pcodedmp_dir)
        )
        
        output = scan_proc.communicate()[0]

        if output.startswith("ERROR:") or output.startswith("WARNING:"):
            self.results["warning"] = True

        elif scan_proc.returncode != 0:
            self.results["warning"] = True
            output = "ERROR: Unexpected output: " + output

        # replace full path
        output = output.replace(target, os.path.basename(target))
        self.results["output"] = output

        return self.results["warning"]
