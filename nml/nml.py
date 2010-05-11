from string import *
import sys, codecs, getopt
from ast import *
from tokens import *
from parser import *
from grfstrings import *
from generic import ScriptError
from actions.sprite_count import SpriteCountAction
from actions.real_sprite import RealSpriteAction
from actions.action8 import Action8
from output_nfo import OutputNFO
from output_grf import OutputGRF

# Build the lexer
import ply.lex as lex
lexer = lex.lex()

def p_error(p):
    if p == None: print "Unexpected EOF"
    else:
        print p
        print "Syntax error at '%s', line %d" % (p.value, p.lineno)
    sys.exit(2)

import ply.yacc as yacc
parser = yacc.yacc(debug=True)

def usage():
    print "Usage: "+sys.argv[0]+" [<options>] <filenames>"
    print """
    where <filenames> are one or more nml files to parse and available options are
    -h, --help: show this help text
    Mind that you must not swap options and arguments. Options MUST go first.
    """

_debug = 0

def main(argv):
    global _debug
    _debug = 0
    retval = 0
    
    try:                  
        opts, args = getopt.getopt(argv, "hd", ["help","debug"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--debug"):
            _debug = 1
    
    read_extra_commands()
    read_lang_files()
    
    if not args:
        raise "TODO: re-implement writing to stdout"
        #retval |= nml(sys.stdin, sys.stdout)
    for arg in args:
        if not os.access(arg, os.R_OK):
            print "Failed to open "+arg
            retval |= 2
        else:
            outputfilename = filename_output_from_input(arg, ".nfo")
            print outputfilename+": parsing "+arg
            input = codecs.open(arg, 'r', 'utf-8')
            output_nfo = OutputNFO(outputfilename)
            output_grf = OutputGRF(filename_output_from_input(arg, ".grf"))
            outputs = (output_nfo, output_grf)
            retval |= nml(input, outputs)
            for output in outputs: output.close()
            input.close()
    sys.exit(retval)

def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext

def nml(inputfile, outputfiles):
    script = inputfile.read().strip()
    if script == "":
        print "Empty input file"
        return 4
    try:
        result = parser.parse(script)
    except:
        print "Error while parsing input file"
        raise
        return 8
    
    if _debug > 0:
        print_script(result, 0)
    
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
