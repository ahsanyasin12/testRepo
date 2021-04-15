import os
import magic
from fame.core.module import ProcessingModule
from fame.common.utils import tempdir


class ACE_Extract(ProcessingModule):
    name = "ace-extract"
    description = "Extract disguised ace archives"

    def is_ace(self, target):
        if "://" in target and target.lower().startswith("http"):
            return False
        return magic.from_file(target).startswith('ACE')

    def add_tag_if_disguised(self, target):
        arch_ext = ['.rar', '.zip', '.arj']
        if target[-4:].lower() in arch_ext:
            self.add_tag('ACE_disguised')

    def extract(self, target):
        tmpdir = tempdir()
        os.system("acefile-unace -d {} -x {}".format(tmpdir, target))
        files = os.popen("acefile-unace -l {}".format(target)).read().split('\n')
        for i in range(len(files)):
            files[i] = tmpdir + '/' + files[i]
        return files

    def each(self, target):
        if self.is_ace(target):
            self.add_tag_if_disguised(target)
            files = self.extract(target)
            for f in files:
                if os.path.isfile(f):
                    self.add_extracted_file(f)
            return True
