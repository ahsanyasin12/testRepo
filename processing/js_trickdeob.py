import os
import re
from base64 import b64decode

from fame.core.module import ProcessingModule
from fame.common.utils import tempdir


class JS_Deobfuscate(ProcessingModule):
    name = "js_deobfuscate_trickbot"
    description = "Extract urls from some obfuscated js"
    acts_on = "javascript"

    def de_base(self, base_sf):
        base_sf = base_sf.strip('"')
        base_sf = base_sf.strip("'")
        base_sf = base_sf.replace("ZZZ", "")
        base_sf = base_sf.replace("RPOJECTS", "")
        if len(base_sf) > 3:
            try:
                return b64decode(base_sf)
            except:
                return False

    def is_url(self, url_candidate):
        return re.match('[a-zA-Z0-9-]{3,24}[.][a-zA-Z]{2,8}', url_candidate)

    def each(self, target):
        url_found = False
        with open(target, 'r') as f:
            buf = f.read()

        var_pattern = """['"][a-zA-Z0-9=/]+['"]"""

        matches = re.findall(var_pattern, buf)
        for base_sf in matches:
            url_candidate = self.de_base(base_sf)
            if url_candidate and self.is_url(url_candidate):
                url_found = True
                self.add_ioc("http://{}".format(url_candidate))

        return url_found
