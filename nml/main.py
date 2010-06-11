import sys, os, codecs, optparse
from ast import *
from parser import *
from tokens import NMLLexer
from grfstrings import *
from nml import generic
from actions.sprite_count import SpriteCountAction
from actions.real_sprite import RealSpriteAction
from actions.action8 import Action8
from actions.action11 import LoadBinaryFile
from output_nfo import OutputNFO

# Build the lexer
lexer = NMLLexer()
lexer.build()

# provide yacc with the tokens
tokens = lexer.tokens

def p_error(p):
    if p is None: print "Unexpected EOF"
    else:
        print p
        print "Syntax error at '%s', line %d" % (p.value, p.lineno)
    sys.exit(2)

import ply.yacc as yacc
parser = yacc.yacc(debug=False)

OutputGRF = None
def get_output_grf():
    global OutputGRF
    if OutputGRF: return OutputGRF
    try:
        from output_grf import OutputGRF
        return OutputGRF
    except ImportError:
        print "PIL (python-imaging) wasn't found, no support for writing grf files"
        sys.exit(3)

def main(argv):
    usage = "Usage: %prog [options] <filename>\n" \
            "Where <filename> is the nml file to parse"

    parser = optparse.OptionParser(usage=usage)
    parser.set_defaults(debug=False, crop=False, compress=True, outputs=[])
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="write the AST to stdout")
    parser.add_option("--grf", dest="grf_filename", metavar="<file>", help="write the resulting grf to <file>")
    parser.add_option("--nfo", dest="nfo_filename", metavar="<file>", help="write nfo output to <file>")
    parser.add_option("-c", action="store_true", dest="crop", help="crop extraneous transparent blue from real sprites")
    parser.add_option("-u", action="store_false", dest="compress", help="save uncompressed data in the grf file")
    parser.add_option("--nml", dest="nml_filename", metavar="<file>", help="write optimized nml to <file>")
    parser.add_option("-o", "--output", dest="outputs", action="append", metavar="<file>", help="write output(nfo/grf) to <file>")
    parser.add_option("-t", "--custom-tags", dest="custom_tags", default="custom_tags.txt",  metavar="<file>", help="Load custom tags from <file> [default: %default]")
    parser.add_option("-l", "--lang-dir", dest="lang_dir", default="lang",  metavar="<dir>", help="Load language files from directory <dir> [default: %default]")
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

    read_extra_commands(opts.custom_tags)
    read_lang_files(opts.lang_dir)

    outputfile_given = (opts.grf_filename or opts.nfo_filename or opts.nml_filename or opts.outputs)

    if not args:
        if not outputfile_given:
            parser.print_help()
            sys.exit(2)
        input = sys.stdin
    elif len(args) > 1:
        raise "Error: only a single nml file can be read per run"
    else:
        input_filename = args[0]
        if not os.access(input_filename, os.R_OK):
            raise generic.ScriptError('Input file "%s" does not exist' % input_filename)
        input = codecs.open(input_filename, 'r', 'utf-8')
        if not outputfile_given:
            opts.grf_filename = filename_output_from_input(input_filename, ".grf")

    outputs = []
    if opts.grf_filename: outputs.append(get_output_grf()(opts.grf_filename, opts.compress, opts.crop))
    if opts.nfo_filename: outputs.append(OutputNFO(opts.nfo_filename))
    nml_output = codecs.open(opts.nml_filename, 'w', 'utf-8') if opts.nml_filename else None
    for output in opts.outputs:
        outroot, outext = os.path.splitext(output)
        outext = outext.lower()
        if outext == '.grf': outputs.append(get_output_grf()(output, opts.compress, opts.crop))
        elif outext == '.nfo': outputs.append(OutputNFO(output))
        elif outext == '.nml':
            print "Use --output-nml <file> to specify nml output"
            sys.exit(2)
        else:
            print "Unknown output format %s" % outext
            sys.exit(2)
    ret = nml(input, opts.debug, outputs, nml_output)
    for output in outputs: output.close()
    input.close()
    sys.exit(ret)

def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext

def nml(inputfile, output_debug, outputfiles, nml_output):
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

    if output_debug > 0:
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
            outputfile.next_sprite(isinstance(action, (RealSpriteAction, LoadBinaryFile)))
            action.write(outputfile)
    return 0

if __name__ == "__main__":
    main(sys.argv[1:])
