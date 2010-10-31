
def print_script(script, indent):
    for r in script:
        r.debug_print(indent)

feature_ids = {
    'FEAT_TRAINS': 0x00,
    'FEAT_ROADVEHS': 0x01,
    'FEAT_SHIPS': 0x02,
    'FEAT_AIRCRAFT': 0x03,
    'FEAT_STATIONS': 0x04,
    'FEAT_CANALS': 0x05,
    'FEAT_BRIDGES': 0x06,
    'FEAT_HOUSES': 0x07,
    'FEAT_GLOBALVARS': 0x08,
    'FEAT_INDUSTRYTILES': 0x09,
    'FEAT_INDUSTRIES': 0x0A,
    'FEAT_CARGOS': 0x0B,
    'FEAT_SOUNDEFFECTS': 0x0C,
    'FEAT_AIRPORTS': 0x0D,
    'FEAT_SIGNALS': 0x0E,
    'FEAT_OBJECTS': 0x0F,
    'FEAT_RAILTYPES': 0x10,
    'FEAT_AIRPORTTILES': 0x11,
}

def parse_feature(expr):
    """
    Parse an expression into a valid feature number.

    @param expr: Expression to parse
    @type expr: L{Expression}

    @return: A constant number representing the parsed feature
    @rtype: L{ConstantNumeric}
    """
    expr = expr.reduce_constant([feature_ids])
    if expr.value not in feature_ids.values():
        raise generic.ScriptError("Invalid feature '%s' encountered." + generic.to_hex(expr.value, 2), expr.pos)
    return expr
