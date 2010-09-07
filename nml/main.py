import sys, os, codecs, optparse
from nml import generic, grfstrings, parser, version_info, output_base, output_nml, output_nfo
from nml.actions import action2var, action8, sprite_count
from nml.ast import general

developmode = False # Give 'nice' error message instead of a stack dump.

version = version_info.get_version()

OutputGRF = None
def get_output_grf():
    global OutputGRF
    if OutputGRF: return OutputGRF
    try:
        from nml.output_grf import OutputGRF
        return OutputGRF
    except ImportError:
        print "PIL (python-imaging) wasn't found, no support for writing grf files"
        sys.exit(3)

def parse_cli(argv):
    """
    Parse the command line, and process options.

    @return: Options, and input filename (if not supplied, use C{sys.stdin}).
    @rtype:  C{tuple} (C{Object}, C{str} or C{None})
    """
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
    opt_parser.add_option("-t", "--custom-tags", dest="custom_tags", default="custom_tags.txt",  metavar="<file>",
                        help="Load custom tags from <file> [default: %default]")
    opt_parser.add_option("-l", "--lang-dir", dest="lang_dir", default="lang",  metavar="<dir>",
                        help="Load language files from directory <dir> [default: %default]")

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

    opts.outputfile_given = (opts.grf_filename or opts.nfo_filename or opts.nml_filename or opts.outputs)

    if not args:
        if not opts.outputfile_given:
            opt_parser.print_help()
            sys.exit(2)
        input_filename = None # Output filenames, but no input -> use stdin.
    elif len(args) > 1:
        print "Error: only a single nml file can be read per run"
        opt_parser.print_help()
        sys.exit(2)
    else:
        input_filename = args[0]
        if not os.access(input_filename, os.R_OK):
            raise generic.ScriptError('Input file "%s" does not exist' % input_filename)

    return opts, input_filename

def main(argv):
    global developmode

    opts, input_filename = parse_cli(argv)

    if opts.stack: developmode = True

    grfstrings.read_extra_commands(opts.custom_tags)
    grfstrings.read_lang_files(opts.lang_dir)

    if input_filename is None:
        input = sys.stdin
    else:
        input = codecs.open(input_filename, 'r', 'utf-8')
        if not opts.outputfile_given:
            opts.grf_filename = filename_output_from_input(input_filename, ".grf")

    outputs = []
    if opts.grf_filename: outputs.append(get_output_grf()(opts.grf_filename, opts.compress, opts.crop))
    if opts.nfo_filename: outputs.append(output_nfo.OutputNFO(opts.nfo_filename))
    if opts.nml_filename: outputs.append(output_nml.OutputNML(opts.nml_filename))
    for output in opts.outputs:
        outroot, outext = os.path.splitext(output)
        outext = outext.lower()
        if outext == '.grf': outputs.append(get_output_grf()(output, opts.compress, opts.crop))
        elif outext == '.nfo': outputs.append(output_nfo.OutputNFO(output))
        elif outext == '.nml': outputs.append(output_nml.OutputNML(output))
        else:
            print "Unknown output format %s" % outext
            sys.exit(2)

    ret = nml(input, opts.debug, outputs)

    input.close()
    sys.exit(ret)

def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext

def nml(inputfile, output_debug, outputfiles):
    generic.OnlyOnce.clear()

    script = inputfile.read()
    if script.strip() == "":
        print "Empty input file"
        return 4
    nml_parser = parser.NMLParser()
    result = nml_parser.parse(script)

    for block in result:
        block.pre_process()

    if output_debug > 0:
        general.print_script(result, 0)

    for outputfile in outputfiles: outputfile.open()

    for outputfile in outputfiles:
        if isinstance(outputfile, output_nml.OutputNML):
            for b in result:
                outputfile.write(str(b))
                outputfile.newline()

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
        if isinstance(outputfile, output_base.OutputBase):
            for action in actions:
                action.write(outputfile)

    for outputfile in outputfiles: outputfile.close()

    return 0

def run():
    try:
        main(sys.argv[1:])

    except generic.ScriptError, ex:
        print >> sys.stderr, "nmlc: %s" % str(ex)

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
                   'version' : version,
                   'msg' : ex_msg,
                   'cli' : sys.argv,
                   'loc' : 'File "%s", line %d, in %s' % (filename, lineno, name) }

        msg = "nmlc: An internal error has occurred:\n" \
              "nmlc-version: %(version)s\n" \
              "Error:      (%(class)s) %(msg)s.\n" \
              "Command:    %(cli)s\n" \
              "Location:   %(loc)s\n" % ex_data

        print >> sys.stderr, msg
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    run()
