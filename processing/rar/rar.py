import os
from rarfile import RarFile

from fame.core.module import ProcessingModule
from fame.common.utils import tempdir


class Rar(ProcessingModule):
    name = "rar"
    description = "Extract files from RAR archive."
    acts_on = ["application/x-rar"]

    def each(self, target):
        tmpdir = tempdir()

        rf = RarFile(target)

        namelist = rf.namelist()

        for name in namelist:
            try:
                rf.extract(name, tmpdir)
                filepath = os.path.join(tmpdir, name,)
                if os.path.isfile(filepath):
                    self.add_extracted_file(filepath)
            except RuntimeError:
                for password in ['virus', 'infected']:
                    try:
                        filepath = rf.extract(name, tmpdir, pwd=password)
                        if os.path.isfile(filepath):
                            self.add_extracted_file(filepath)
                        break
                    except RuntimeError:
                        pass
                else:
                    self.log('error', 'Could not extract {}'.format(name))

        return True
