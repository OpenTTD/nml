import sys, os, codecs, optparse
from nml import ast, generic, grfstrings, parser
from nml.actions import action2var, action8, sprite_count
from output_nfo import OutputNFO

developmode = False # Give 'nice' error message instead of a stack dump.

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

try:
    from nml import __version__
    version = __version__.version
except ImportError:
    version = 'unknown'

def main(argv):
    global developmode

    usage = "Usage: %prog [options] <filename>\n" \
            "Where <filename> is the nml file to parse"

    opt_parser = optparse.OptionParser(usage=usage, version=version)
    opt_parser.set_defaults(debug=False, crop=False, compress=True, outputs=[])
    opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="write the AST to stdout")
    opt_parser.add_option("-s", "--stack", action="store_true", dest="stack", help="Dump stack when an error occurs")
    opt_parser.add_option("--grf", dest="grf_filename", metavar="<file>", help="write the resulting grf to <file>")
    opt_parser.add_option("--nfo", dest="nfo_filename", metavar="<file>", help="write nfo output to <file>")
    opt_parser.add_option("-c", action="store_true", dest="crop", help="crop extraneous transparent blue from real sprites")
    opt_parser.add_option("-u", action="store_false", dest="compress", help="save uncompressed data in the grf file")
    opt_parser.add_option("--nml", dest="nml_filename", metavar="<file>", help="write optimized nml to <file>")
    opt_parser.add_option("-o", "--output", dest="outputs", action="append", metavar="<file>", help="write output(nfo/grf) to <file>")
    opt_parser.add_option("-t", "--custom-tags", dest="custom_tags", default="custom_tags.txt",  metavar="<file>", help="Load custom tags from <file> [default: %default]")
    opt_parser.add_option("-l", "--lang-dir", dest="lang_dir", default="lang",  metavar="<dir>", help="Load language files from directory <dir> [default: %default]")
    try:
        opts, args = opt_parser.parse_args(argv)
    except optparse.OptionError, err:
        print "Error while parsing arguments: ", err
        opt_parser.print_help()
        sys.exit(2)
    except TypeError, err:
        print "Error while parsing arguments: ", err
        opt_parser.print_help()
        sys.exit(2)

    if opts.stack: developmode = True

    grfstrings.read_extra_commands(opts.custom_tags)
    grfstrings.read_lang_files(opts.lang_dir)

    outputfile_given = (opts.grf_filename or opts.nfo_filename or opts.nml_filename or opts.outputs)

    if not args:
        if not outputfile_given:
            opt_parser.print_help()
            sys.exit(2)
        input = sys.stdin
    elif len(args) > 1:
        print "Error: only a single nml file can be read per run"
        opt_parser.print_help()
        sys.exit(2)
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
    if nml_output is not None:
        nml_output.close()
    input.close()

    sys.exit(ret)

def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext

def nml(inputfile, output_debug, outputfiles, nml_output):
    script = inputfile.read()
    if script.strip() == "":
        print "Empty input file"
        return 4
    nml_parser = parser.NMLParser()
    try:
        result = nml_parser.parse(script)
    except:
        print "Error while parsing input file"
        raise
        return 8

    if output_debug > 0:
        ast.print_script(result, 0)

    if nml_output is not None:
        for b in result:
            nml_output.write(str(b))
            nml_output.write('\n')

    actions = []
    for block in result:
        actions.extend(block.get_action_list())

    has_action8 = False
    for i in range(len(actions) - 1, -1, -1):
        if isinstance(actions[i], action2var.Action2Var):
            actions[i].resolve_tmp_storage()
        elif isinstance(actions[i], action8.Action8):
            has_action8 = True

    if has_action8:
        actions = [sprite_count.SpriteCountAction(len(actions))] + actions

    for action in actions:
        action.prepare_output()
    for outputfile in outputfiles:
        for action in actions:
            action.write(outputfile)
    return 0

def run():
    try:
        main(sys.argv[1:])

    except generic.ScriptError, ex:
        print >> sys.stderr, "NML: %s" % ex

        if developmode: raise # Reraise exception in developmode
        sys.exit(1)

    except SystemExit, ex:
        raise

    except KeyboardInterrupt, ex:
        print 'Application forcibly terminated by user.'

        if developmode: raise # Reraise exception in developmode

        sys.exit(1)

    except Exception, ex: # Other/internal error.

        if developmode: raise # Reraise exception in developmode

        # User mode: print user friendly error message.
        ex_msg = str(ex)
        if len(ex_msg) > 0: ex_msg = '"%s"' % ex_msg

        traceback = sys.exc_info()[2]
        # Walk through the traceback object until we get to the point where the exception happened.
        while traceback.tb_next is not None:
            traceback = traceback.tb_next

        lineno = traceback.tb_lineno
        frame = traceback.tb_frame
        code = frame.f_code
        filename = code.co_filename
        name = code.co_name
        del traceback # Required according to Python docs.

        ex_data = {'class' : ex.__class__.__name__,
                   'msg' : ex_msg,
                   'cli' : sys.argv,
                   'loc' : 'File "%s", line %d, in %s' % (filename, lineno, name) }

        msg = "NML: An internal error has occurred:\n" \
              "Error:    (%(class)s) %(msg)s.\n" \
              "Command:  %(cli)s\n" \
              "Location: %(loc)s\n" % ex_data

        print >> sys.stderr, msg
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    run()
