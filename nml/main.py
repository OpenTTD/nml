import sys, os, codecs, optparse
from nml import generic, grfstrings, parser, version_info, output_base, output_nml, output_nfo, output_grf, output_dep, palette
from nml.actions import action2layout, action2var, action8, sprite_count, real_sprite, action4, action0, action1, action11
from nml.ast import general, grf, alt_sprites

try:
    import Image
except ImportError:
    pass

developmode = False # Give 'nice' error message instead of a stack dump.

version = version_info.get_nml_version()

def parse_cli(argv):
    """
    Parse the command line, and process options.

    @return: Options, and input filename (if not supplied, use C{sys.stdin}).
    @rtype:  C{tuple} (C{Object}, C{str} or C{None})
    """
    usage = "Usage: %prog [options] <filename>\n" \
            "Where <filename> is the nml file to parse"

    opt_parser = optparse.OptionParser(usage=usage, version=version_info.get_cli_version())
    opt_parser.set_defaults(debug=False, crop=False, compress=True, outputs=[], start_sprite_num=0,
                            custom_tags="custom_tags.txt", lang_dir="lang", sprites_dir="sprites", default_lang="english.lng",
                            forced_palette="ANY")
    opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="write the AST to stdout")
    opt_parser.add_option("-s", "--stack", action="store_true", dest="stack", help="Dump stack when an error occurs")
    opt_parser.add_option("--grf", dest="grf_filename", metavar="<file>", help="write the resulting grf to <file>")
    opt_parser.add_option("--nfo", dest="nfo_filename", metavar="<file>", help="write nfo output to <file>")
    opt_parser.add_option("-M", dest="dep_filename", metavar="<file>", help="write graphics dependencies to <file> (requires --grf or input file)")
    opt_parser.add_option("-c", action="store_true", dest="crop", help="crop extraneous transparent blue from real sprites")
    opt_parser.add_option("-u", action="store_false", dest="compress", help="save uncompressed data in the grf file")
    opt_parser.add_option("--nml", dest="nml_filename", metavar="<file>", help="write optimized nml to <file>")
    opt_parser.add_option("-o", "--output", dest="outputs", action="append", metavar="<file>", help="write output(nfo/grf) to <file>")
    opt_parser.add_option("-t", "--custom-tags", dest="custom_tags", metavar="<file>",
                        help="Load custom tags from <file> [default: %default]")
    opt_parser.add_option("-l", "--lang-dir", dest="lang_dir", metavar="<dir>",
                        help="Load language files from directory <dir> [default: %default]")
    opt_parser.add_option("-a", "--sprites-dir", dest="sprites_dir", metavar="<dir>",
                        help="Store 32bpp sprites in directory <dir> [default: %default]")
    opt_parser.add_option("--default-lang", dest="default_lang", metavar="<file>",
                        help="The default language is stored in <file> [default: %default]")
    opt_parser.add_option("--start-sprite", action="store", type="int", dest="start_sprite_num", metavar="<num>",
                        help="Set the first sprite number to write (do not use except when you output nfo that you want to include in other files)")
    opt_parser.add_option("-p", "--palette", dest="forced_palette", metavar="<palette>", choices = ["DOS", "WIN", "ANY"],
                        help="Force nml to use the palette <pal> [default: %default]. Valid values are 'DOS', 'WIN', 'ANY'")

    opts, args = opt_parser.parse_args(argv)

    opts.outputfile_given = (opts.grf_filename or opts.nfo_filename or opts.nml_filename or opts.dep_filename or opts.outputs)

    if not args:
        if not opts.outputfile_given:
            opt_parser.print_help()
            sys.exit(2)
        input_filename = None # Output filenames, but no input -> use stdin.
    elif len(args) > 1:
        opt_parser.error("Error: only a single nml file can be read per run")
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
    grfstrings.read_lang_files(opts.lang_dir, opts.default_lang)

    if input_filename is None:
        input = sys.stdin
    else:
        input = codecs.open(input_filename, 'r', 'utf-8')
        if not opts.outputfile_given:
            opts.grf_filename = filename_output_from_input(input_filename, ".grf")

    outputs = []
    if opts.grf_filename: outputs.append(output_grf.OutputGRF(opts.grf_filename, opts.compress, opts.crop))
    if opts.nfo_filename: outputs.append(output_nfo.OutputNFO(opts.nfo_filename, opts.start_sprite_num))
    if opts.nml_filename: outputs.append(output_nml.OutputNML(opts.nml_filename))
    if opts.dep_filename:
        depgrf_filename = None
        if opts.grf_filename:
            depgrf_filename = opts.grf_filename
        if depgrf_filename is None and input_filename is not None:
            depgrf_filename = filename_output_from_input(input_filename, ".grf")
        if depgrf_filename is None:
            raise generic.ScriptError("-M <file> requires additionally an input filename or valid filename for output via --grf.")
        else:
            outputs.append(output_dep.OutputDEP(opts.dep_filename, depgrf_filename))
    for output in opts.outputs:
        outroot, outext = os.path.splitext(output)
        outext = outext.lower()
        if outext == '.grf': outputs.append(output_grf.OutputGRF(output, opts.compress, opts.crop))
        elif outext == '.nfo': outputs.append(output_nfo.OutputNFO(output, opts.start_sprite_num))
        elif outext == '.nml': outputs.append(output_nml.OutputNML(output))
        elif outext == '.dep': outputs.append(output_dep.OutputDEP(output, opts.grf_filename))
        else:
            generic.print_warning("Unknown output format %s" % outext)
            sys.exit(2)

    ret = nml(input, opts.debug, outputs, opts.sprites_dir, opts.start_sprite_num, opts.forced_palette)

    input.close()
    sys.exit(ret)

def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext

def nml(inputfile, output_debug, outputfiles, sprites_dir, start_sprite_num, forced_palette):
    generic.OnlyOnce.clear()

    script = inputfile.read()
    # Strip a possible BOM
    script = script.lstrip(unicode(codecs.BOM_UTF8, "utf-8"))

    if script.strip() == "":
        generic.print_warning("Empty input file")
        return 4
    nml_parser = parser.NMLParser()
    result = nml_parser.parse(script)
    result.validate([])

    if output_debug > 0:
        result.debug_print(0)

    for outputfile in outputfiles:
        if isinstance(outputfile, output_nml.OutputNML):
            outputfile.open()
            outputfile.write(str(result))
            outputfile.close()

    result.register_names()
    result.pre_process()
    tmp_actions = result.get_action_list()

    actions = []
    for action in tmp_actions:
        if isinstance(action, action1.SpritesetCollection):
            actions.extend(action.get_action_list())
        else:
            actions.append(action)
    actions.extend(action11.get_sound_actions())

    action8_index = -1
    for i in range(len(actions) - 1, -1, -1):
        if isinstance(actions[i], (action2var.Action2Var, action2layout.Action2Layout)):
            actions[i].resolve_tmp_storage()
        elif isinstance(actions[i], action8.Action8):
            action8_index = i

    if action8_index != -1:
        lang_actions = []
        # Add plural/gender/case tables
        for lang_pair in grfstrings.langs:
            lang_id, lang = lang_pair
            lang_actions.extend(action0.get_language_translation_tables(lang))
        # Add global strings
        lang_actions.extend(action4.get_global_string_actions())
        actions = actions[:action8_index + 1] + lang_actions + actions[action8_index + 1:]

    sprite_files = set()
    for action in actions:
        if isinstance(action, real_sprite.RealSpriteAction) and not isinstance(action, real_sprite.RecolourSpriteAction):
            if action.sprite.is_empty: continue
            action.sprite.validate_size()
            sprite_files.add(action.sprite.file.value)

    # Check whether we can terminate sprite processing prematurely for
    #     dependency checks
    skip_sprite_processing = True
    for outputfile in outputfiles:
        if isinstance(outputfile, output_dep.OutputDEP):
            outputfile.open()
            for f in sprite_files:
                outputfile.write(f)
            outputfile.close()
        skip_sprite_processing &= outputfile.skip_sprite_checks()

    if skip_sprite_processing: return 0

    if not Image and len(sprite_files) > 0:
        generic.print_warning("PIL (python-imaging) wasn't found, no support for using graphics")
        sys.exit(3)

    used_palette = forced_palette
    last_file = None
    for f in sprite_files:
        if not os.path.exists(f):
            raise generic.ImageError("File doesn't exist", f)
        try:
            im = Image.open(f)
        except IOError, ex:
            raise generic.ImageError(str(ex), f)
        if im.mode != "P":
            raise generic.ImageError("image does not have a palette", f)
        pal = palette.validate_palette(im, f)

        if forced_palette != "ANY" and pal != forced_palette and not (forced_palette == "DOS" and pal == "WIN"):
            raise generic.ImageError("Image has '%s' palette, but you forced the '%s' palette" % (pal, used_palette), f)

        if used_palette == "ANY":
            used_palette = pal
        elif pal != used_palette:
            if used_palette in ("WIN", "DOS") and pal in ("WIN", "DOS"):
                used_palette = "DOS"
            else:
                raise generic.ImageError("Image has '%s' palette, but \"%s\" has the '%s' palette" % (pal, last_file, used_palette), f)
        last_file = f

    palette_bytes = {"WIN": "W", "DOS": "D", "ANY": "A"}
    if used_palette in palette_bytes:
        grf.set_palette_used(palette_bytes[used_palette])
    for outputfile in outputfiles:
        outputfile.palette = used_palette

    if action8_index != -1:
        actions = [sprite_count.SpriteCountAction(len(actions))] + actions

    block_names = {}
    for idx, action in enumerate(actions):
        num = start_sprite_num + idx
        action.prepare_output()
        if isinstance(action, real_sprite.RealSpriteAction):
            if action.block_name:
                block_names[action.block_name] = num
            if action.sprite_num is not None:
                if action.sprite_num.value != num:
                    raise generic.ScriptError("Sprite number %d given in base_sprites-block, but it doesn't match output sprite number %d" % (action.sprite_num.value, num))

    for outputfile in outputfiles:
        if isinstance(outputfile, output_base.BinaryOutputBase):
            outputfile.open()
            for action in actions:
                action.write(outputfile)
            outputfile.close()

    for block in alt_sprites.alt_sprites_list:
        block.process(sprites_dir, block_names)

    return 0

def run():
    try:
        main(sys.argv[1:])

    except generic.ScriptError, ex:
        generic.print_warning("nmlc: %s" % str(ex))

        if developmode: raise # Reraise exception in developmode
        sys.exit(1)

    except SystemExit, ex:
        raise

    except KeyboardInterrupt, ex:
        generic.print_warning('Application forcibly terminated by user.')

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

        generic.print_warning(msg)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    run()
