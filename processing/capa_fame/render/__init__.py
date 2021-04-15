import capa.render

def render_fame(meta, rules, capabilities):
    from r_fame import r_fame

    doc = capa.render.convert_capabilities_to_result_document(meta, rules, capabilities)
    return r_fame(doc)
