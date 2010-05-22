from string import *
import sys, codecs, optparse
from ast import *
from parser import *
from tokens import NMLLexer
from grfstrings import *
from generic import ScriptError
from actions.sprite_count import SpriteCountAction
from actions.real_sprite import RealSpriteAction
from actions.action8 import Action8
from output_nfo import OutputNFO

# Build the lexer
lexer = NMLLexer()
lexer.build()

# provide yacc with the tokens
tokens = lexer.tokens

def p_error(p):
    if p == None: print "Unexpected EOF"
    else:
        print p
        print "Syntax error at '%s', line %d" % (p.value, p.lineno)
    sys.exit(2)

import ply.yacc as yacc
parser = yacc.yacc(debug=True)

_debug = 0
crop_sprites = False
compress_grf = True

def main(argv):
    global _debug, crop_sprites, compress_grf
    _debug = 0
    retval = 0
    usage = """Usage: %prog [options] <filename>\nWhere <filename> is the nml file to parse"""
    # that above line should really contain _real_ newlines, but that's really not readable without strange indentation
    parser = optparse.OptionParser(usage=usage)
    parser.set_defaults(debug=False, crop=False, compress=True)
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="write the AST to stdout")
    parser.add_option("-o", "--grf", dest="grf_filename", metavar="<file>", help="write the resulting grf to <file>")
    parser.add_option("--nfo", dest="nfo_filename", metavar="<file>", help="write nfo output to <file>")
    parser.add_option("-c", action="store_true", dest="crop", help="crop extraneous transparent blue from real sprites")
    parser.add_option("-u", action="store_false", dest="compress", help="save uncompressed data in the grf file")
    parser.add_option("--nml", dest="nml_filename", metavar="<file>", help="write optimized nml to <file>")
    try:
        opts, args = parser.parse_args(argv)
    except optparse.OptionError, err:
        print "Error while parsing arguments: ", err
        parser.print_help()
        sys.exit(2)
    except TypeError, err:
        print "Error while parsing arguments: ", err
        parser.print_help()
        sys.exit(2)

    if opts.debug:
        _debug = 1
    crop_sprites = opts.crop
    compress_grf = opts.compress

    read_extra_commands()
    read_lang_files()

    outputfile_given = (opts.grf_filename or opts.nfo_filename or opts.nml_filename)

    if not args:
        if not outputfile_given:
            parser.print_help()
            sys.exit(2)
        input = sys.stdin
    elif len(args) > 1:
        raise "Error: only a single nml file can be read per run"
    else:
        input_filename = args[0]
        input = codecs.open(input_filename, 'r', 'utf-8')
        if not outputfile_given:
            opts.grf_filename = filename_output_from_input(input_filename, ".grf")

    outputs = []
    if opts.grf_filename:
        try:
            from output_grf import OutputGRF
            outputs.append(OutputGRF(opts.grf_filename))
        except ImportError:
            print "PIL (python-imaging) wasn't found, no support for writing grf files"
            sys.exit(3)
    if opts.nfo_filename: outputs.append(OutputNFO(opts.nfo_filename))
    nml_output = codecs.open(opts.nml_filename, 'w', 'utf-8') if opts.nml_filename else None
    ret = nml(input, outputs, nml_output)
    for output in outputs: output.close()
    input.close()
    sys.exit(ret)

def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext

def nml(inputfile, outputfiles, nml_output):
    script = inputfile.read().strip()
    if script == "":
        print "Empty input file"
        return 4
    try:
        result = parser.parse(script, lexer=lexer.lexer)
    except:
        print "Error while parsing input file"
        raise
        return 8

    if _debug > 0:
        print_script(result, 0)

    if nml_output is not None:
        for b in result:
            nml_output.write(str(b))
            nml_output.write('\n')

    actions = []
    for block in result:
        actions.extend(block.get_action_list())

    has_action8 = False
    for i in range(len(actions) - 1, -1, -1):
        if isinstance(actions[i], Action2Var):
            actions[i].resolve_tmp_storage()
        elif isinstance(actions[i], Action8):
            has_action8 = True

    if has_action8:
        actions = [SpriteCountAction(len(actions))] + actions

    for action in actions:
        action.prepare_output()
    for outputfile in outputfiles:
        for action in actions:
            outputfile.next_sprite(isinstance(action, RealSpriteAction))
            action.write(outputfile)
    return 0

if __name__ == "__main__":
    main(sys.argv[1:])
