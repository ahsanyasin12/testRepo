import re

from fame.core.module import ProcessingModule

class JS_Deobfuscate_Type2(ProcessingModule):
    name = "js_deobfuscate_generic_2"
    description = "Extract urls from some obfuscated js"
    acts_on = "javascript"

    def is_url(self, url_candidate):
        return re.search("[a-zA-Z0-9-]{3,}[.][a-zA-Z]{2,3}", url_candidate)

    def each(self, target):
        url_found = False
        with open(target, 'r') as f:
            buf = f.read()

        var_pattern = """var\s.*?['"](.*?)['"][.]split[(]['"](.*?)['"][)][.]join[(]"""

        matches = re.findall(var_pattern, buf)
        for m in matches:
            url_candidate = m[0].replace(m[1], "")
            if self.is_url(url_candidate):
                url_found = True
                if url_candidate.startswith('http'):
                    self.add_ioc("{}".format(url_candidate))
                else:
                    self.add_ioc("http://{}".format(url_candidate))
        return url_found
