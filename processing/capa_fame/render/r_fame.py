# Copyright (C) 2020 FireEye, Inc. All Rights Reserved.
# created by FireEye
# edited by Richard Weiss: Adapted renderer for FAME

import collections
import six
import tabulate
import capa.render.utils

def test():
    return 0

def render_meta(doc):
    rows = [
        ('md5', doc['meta']['sample']['md5']),
        ('path', doc['meta']['sample']['path']),
    ]

    return rows


def render_capabilities(doc):
    rows = []
    for rule in capa.render.utils.capability_rules(doc):
        count = len(rule["matches"])
        if count == 1:
            capability = rule["meta"]["name"]
        else:
            capability = "%s (%d matches)" % (rule["meta"]["name"], count)
        rows.append((capability, rule["meta"]["namespace"]))

    return rows


def render_attack(doc):
    tactics = collections.defaultdict(set)
    for rule in capa.render.utils.capability_rules(doc):
        if not rule["meta"].get("att&ck"):
            continue

        for attack in rule["meta"]["att&ck"]:
            tactic, _, rest = attack.partition("::")
            if "::" in rest:
                technique, _, rest = rest.partition("::")
                subtechnique, _, id = rest.rpartition(" ")
                tactics[tactic].add((technique, subtechnique, id))
            else:
                technique, _, id = rest.rpartition(" ")
                tactics[tactic].add((technique, id))

    rows = []
    for tactic, techniques in sorted(tactics.items()):
        inner_rows = []
        for spec in sorted(techniques):
            if len(spec) == 2:
                technique, id = spec
                inner_rows.append("%s %s" % (technique, id))
            elif len(spec) == 3:
                technique, subtechnique, id = spec
                inner_rows.append("%s::%s %s" % (technique, subtechnique, id))
            else:
                raise RuntimeError("unexpected ATT&CK spec format")
        rows.append((tactic.upper(), "\n".join(inner_rows),))

    return rows


def r_fame(doc):
    results = {}

    results['meta'] = render_meta(doc)
    results['attack'] = render_attack(doc)
    results['capabilities'] = render_capabilities(doc)

    return results
