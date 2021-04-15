
# Yara zipped documents

Module to look for YARA patterns inside zompressed documents like DOCX, XLSX or ODT compressed documents. It extracts `.xml` and `.rels` files and applies given compiled yara file to them.

Based on [CERT Société Générale > fame_module > ZIP module](https://github.com/certsocietegenerale/fame_modules/blob/master/processing/zip/zip.py)