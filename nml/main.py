__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

import codecs
import optparse
import os
import sys

from nml import (
    generic,
    global_constants,
    grfstrings,
    output_dep,
    output_grf,
    output_nfo,
    output_nml,
    palette,
    parser,
    spritecache,
    spriteencoder,
    version_info,
)
from nml.actions import (
    action0,
    action1,
    action2,
    action2layout,
    action2var,
    action4,
    action6,
    action7,
    action8,
    action11,
    actionF,
    real_sprite,
    sprite_count,
)
from nml.ast import alt_sprites, grf

try:
    from PIL import Image
except ImportError:
    # Image is required only when using graphics
    pass

developmode = False  # Give 'nice' error message instead of a stack dump.

version = version_info.get_nml_version()


def parse_cli(argv):
    """
    Parse the command line, and process options.

    @return: Options, and input filename (if not supplied, use C{sys.stdin}).
    @rtype:  C{tuple} (C{Object}, C{str} or C{None})
    """
    usage = "Usage: %prog [options] <filename>\n" "Where <filename> is the nml file to parse"

    opt_parser = optparse.OptionParser(usage=usage, version=version_info.get_cli_version())
    opt_parser.set_defaults(
        debug=False,
        crop=False,
        compress=True,
        outputs=[],
        start_sprite_num=0,
        custom_tags="custom_tags.txt",
        lang_dir="lang",
        default_lang="english.lng",
        cache_dir=".nmlcache",
        forced_palette="ANY",
        quiet=False,
        md5_filename=None,
        keep_orphaned=True,
        verbosity=generic.verbosity_level,
        rebuild_parser=False,
        debug_parser=False,
    )
    opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="write the AST to stdout")
    opt_parser.add_option("-s", "--stack", action="store_true", dest="stack", help="Dump stack when an error occurs")
    opt_parser.add_option("--grf", dest="grf_filename", metavar="<file>", help="write the resulting grf to <file>")
    opt_parser.add_option(
        "--md5", dest="md5_filename", metavar="<file>", help="Write an md5sum of the resulting grf to <file>"
    )
    opt_parser.add_option("--nfo", dest="nfo_filename", metavar="<file>", help="write nfo output to <file>")
    opt_parser.add_option(
        "-M",
        action="store_true",
        dest="dep_check",
        help=(
            "output a rule suitable for make describing"
            " the graphics dependencies of the main grf file (requires input file or --grf)"
        ),
    )
    opt_parser.add_option(
        "--MF",
        dest="dep_filename",
        metavar="<file>",
        help="When used with -M, specifies a file to write the dependencies to",
    )
    opt_parser.add_option(
        "--MT",
        dest="depgrf_filename",
        metavar="<file>",
        help="target of the rule emitted by dependency generation (requires -M)",
    )
    opt_parser.add_option(
        "-c", action="store_true", dest="crop", help="crop extraneous transparent blue from real sprites"
    )
    opt_parser.add_option("-u", action="store_false", dest="compress", help="save uncompressed data in the grf file")
    opt_parser.add_option("--nml", dest="nml_filename", metavar="<file>", help="write optimized nml to <file>")
    opt_parser.add_option(
        "-o", "--output", dest="outputs", action="append", metavar="<file>", help="write output(nfo/grf) to <file>"
    )
    opt_parser.add_option(
        "-t",
        "--custom-tags",
        dest="custom_tags",
        metavar="<file>",
        help="Load custom tags from <file> [default: %default]",
    )
    opt_parser.add_option(
        "-l",
        "--lang-dir",
        dest="lang_dir",
        metavar="<dir>",
        help="Load language files from directory <dir> [default: %default]",
    )
    opt_parser.add_option(
        "--default-lang",
        dest="default_lang",
        metavar="<file>",
        help="The default language is stored in <file> [default: %default]",
    )
    opt_parser.add_option(
        "--start-sprite",
        action="store",
        type="int",
        dest="start_sprite_num",
        metavar="<num>",
        help=(
            "Set the first sprite number to write"
            " (do not use except when you output nfo that you want to include in other files)"
        ),
    )
    opt_parser.add_option(
        "-p",
        "--palette",
        dest="forced_palette",
        metavar="<palette>",
        choices=["DEFAULT", "LEGACY", "DOS", "WIN", "ANY"],
        help="Force nml to use the palette <pal> [default: %default]. Valid values are 'DEFAULT', 'LEGACY', 'ANY'",
    )
    opt_parser.add_option(
        "--quiet", action="store_true", dest="quiet", help="Disable all warnings. Errors will be printed normally."
    )
    opt_parser.add_option(
        "-n",
        "--no-cache",
        action="store_true",
        dest="no_cache",
        help="Disable caching of sprites in .cache[index] files, which may reduce compilation time.",
    )
    opt_parser.add_option(
        "--cache-dir",
        dest="cache_dir",
        metavar="<dir>",
        help="Cache files are stored in directory <dir> [default: %default]",
    )
    opt_parser.add_option(
        "--clear-orphaned",
        action="store_false",
        dest="keep_orphaned",
        help="Remove unused/orphaned items from cache files.",
    )
    opt_parser.add_option(
        "--verbosity",
        type="int",
        dest="verbosity",
        metavar="<level>",
        help="Set the verbosity level for informational output. [default: %default, max: {}]".format(
            generic.VERBOSITY_MAX
        ),
    )
    opt_parser.add_option(
        "-R",
        "--rebuild-parser",
        action="store_true",
        dest="rebuild_parser",
        help="Force regeneration of parser tables.",
    )
    opt_parser.add_option(
        "-D", "--debug-parser", action="store_true", dest="debug_parser", help="Enable debug mode for parser."
    )

    opts, args = opt_parser.parse_args(argv)

    generic.set_verbosity(0 if opts.quiet else opts.verbosity)
    generic.set_cache_root_dir(None if opts.no_cache else opts.cache_dir)
    spritecache.keep_orphaned = opts.keep_orphaned

    opts.outputfile_given = (
        opts.grf_filename or opts.nfo_filename or opts.nml_filename or opts.dep_filename or opts.outputs
    )

    if not args:
        if not opts.outputfile_given:
            opt_parser.print_help()
            sys.exit(2)
        input_filename = None  # Output filenames, but no input -> use stdin.
    elif len(args) > 1:
        opt_parser.error("Error: only a single nml file can be read per run")
    else:
        input_filename = args[0]
        if not os.access(input_filename, os.R_OK):
            raise generic.ScriptError('Input file "{}" does not exist'.format(input_filename))

    return opts, input_filename


def main(argv):
    global developmode

    opts, input_filename = parse_cli(argv)

    if opts.stack:
        developmode = True

    grfstrings.read_extra_commands(opts.custom_tags)

    generic.print_progress("Reading lang ...")

    grfstrings.read_lang_files(opts.lang_dir, opts.default_lang)

    generic.clear_progress()

    # We have to do the dependency check first or we might later have
    #   more targets than we asked for
    outputs = []
    if opts.dep_check:
        # First make sure we have a file to output the dependencies to:
        dep_filename = opts.dep_filename
        if dep_filename is None and opts.grf_filename is not None:
            dep_filename = filename_output_from_input(opts.grf_filename, ".dep")
        if dep_filename is None and input_filename is not None:
            dep_filename = filename_output_from_input(input_filename, ".dep")
        if dep_filename is None:
            raise generic.ScriptError(
                "-M requires a dependency file either via -MF, an input filename or a valid output via --grf"
            )

        # Now make sure we have a file which is the target for the dependencies:
        depgrf_filename = opts.depgrf_filename
        if depgrf_filename is None and opts.grf_filename is not None:
            depgrf_filename = opts.grf_filename
        if depgrf_filename is None and input_filename is not None:
            depgrf_filename = filename_output_from_input(input_filename, ".grf")
        if depgrf_filename is None:
            raise generic.ScriptError(
                "-M requires either a target grf file via -MT, an input filename or a valid output via --grf"
            )

        # Only append the dependency check to the output targets when we have both,
        #   a target grf and a file to write to
        if dep_filename is not None and depgrf_filename is not None:
            outputs.append(output_dep.OutputDEP(dep_filename, depgrf_filename))

    if input_filename is None:
        input = sys.stdin
    else:
        input = codecs.open(generic.find_file(input_filename), "r", "utf-8")
        # Only append an output grf name, if no ouput is given, also not implicitly via -M
        if not opts.outputfile_given and not outputs:
            opts.grf_filename = filename_output_from_input(input_filename, ".grf")

    # Translate the 'common' palette names as used by OpenTTD to the traditional ones being within NML's code
    if opts.forced_palette == "DOS":
        opts.forced_palette = "DEFAULT"
    elif opts.forced_palette == "WIN":
        opts.forced_palette = "LEGACY"

    if opts.grf_filename:
        outputs.append(output_grf.OutputGRF(opts.grf_filename))
    if opts.nfo_filename:
        outputs.append(output_nfo.OutputNFO(opts.nfo_filename, opts.start_sprite_num))
    if opts.nml_filename:
        outputs.append(output_nml.OutputNML(opts.nml_filename))

    for output in opts.outputs:
        outroot, outext = os.path.splitext(output)
        outext = outext.lower()
        if outext == ".grf":
            outputs.append(output_grf.OutputGRF(output))
        elif outext == ".nfo":
            outputs.append(output_nfo.OutputNFO(output, opts.start_sprite_num))
        elif outext == ".nml":
            outputs.append(output_nml.OutputNML(output))
        elif outext == ".dep":
            outputs.append(output_dep.OutputDEP(output, opts.grf_filename))
        else:
            generic.print_error("Unknown output format {}".format(outext))
            sys.exit(2)

    ret = nml(
        input,
        input_filename,
        opts.debug,
        outputs,
        opts.start_sprite_num,
        opts.compress,
        opts.crop,
        opts.forced_palette,
        opts.md5_filename,
        opts.rebuild_parser,
        opts.debug_parser,
    )

    input.close()
    sys.exit(ret)


def filename_output_from_input(name, ext):
    return os.path.splitext(name)[0] + ext


def nml(
    inputfile,
    input_filename,
    output_debug,
    outputfiles,
    start_sprite_num,
    compress_grf,
    crop_sprites,
    forced_palette,
    md5_filename,
    rebuild_parser,
    debug_parser,
):
    """
    Compile an NML file.

    @param inputfile: File handle associated with the input file.
    @type  inputfile: C{File}

    @param input_filename: Filename of the input file, C{None} if receiving from L{sys.stdin}
    @type  input_filename: C{str} or C{None}

    @param outputfiles: Output streams to write to.
    @type  outputfiles: C{List} of L{output_base.OutputBase}

    @param start_sprite_num: Number of the first sprite.
    @type  start_sprite_num: C{int}

    @param compress_grf: Enable GRF sprite compression.
    @type  compress_grf: C{bool}

    @param crop_sprites: Enable sprite cropping.
    @type  crop_sprites: C{bool}

    @param forced_palette: Palette to use for the file.
    @type  forced_palette: C{str}

    @param md5_filename: Filename to use for writing the md5 sum of the grf file.
                         C{None} if the file should not be written.
    @type  md5_filename: C{str} or C{None}
    """
    generic.OnlyOnce.clear()

    generic.print_progress("Reading ...")

    try:
        script = inputfile.read()
    except UnicodeDecodeError as ex:
        raise generic.ScriptError("Input file is not utf-8 encoded: {}".format(ex))
    # Strip a possible BOM
    script = script.lstrip(str(codecs.BOM_UTF8, "utf-8"))

    if script.strip() == "":
        generic.print_error("Empty input file")
        return 4

    generic.print_progress("Init parser ...")

    nml_parser = parser.NMLParser(rebuild_parser, debug_parser)
    if input_filename is None:
        input_filename = "input"

    generic.print_progress("Parsing ...")

    result = nml_parser.parse(script, input_filename)
    result.validate([])

    if output_debug > 0:
        result.debug_print(0)

    for outputfile in outputfiles:
        if isinstance(outputfile, output_nml.OutputNML):
            with outputfile:
                outputfile.write(str(result))

    generic.print_progress("Preprocessing ...")

    result.register_names()
    result.pre_process()
    tmp_actions = result.get_action_list()

    generic.print_progress("Generating actions ...")

    actions = []
    for action in tmp_actions:
        if isinstance(action, action1.SpritesetCollection):
            actions.extend(action.get_action_list())
        else:
            actions.append(action)
    actions.extend(action11.get_sound_actions())

    generic.print_progress("Assigning Action2 registers ...")

    action8_index = -1
    for i in range(len(actions) - 1, -1, -1):
        if isinstance(actions[i], (action2var.Action2Var, action2layout.Action2Layout)):
            actions[i].resolve_tmp_storage()
        elif isinstance(actions[i], action8.Action8):
            action8_index = i

    generic.print_progress("Generating strings ...")

    if action8_index != -1:
        lang_actions = []
        # Add plural/gender/case tables
        for lang_pair in grfstrings.langs:
            lang_id, lang = lang_pair
            lang_actions.extend(action0.get_language_translation_tables(lang))
        # Add global strings
        lang_actions.extend(action4.get_global_string_actions())
        actions = actions[: action8_index + 1] + lang_actions + actions[action8_index + 1 :]

    generic.print_progress("Collecting real sprites ...")

    # Collect all sprite files, and put them into buckets of same image and mask files
    sprite_files = {}
    for action in actions:
        if isinstance(action, real_sprite.RealSpriteAction):
            for sprite in action.sprite_list:
                if sprite.is_empty:
                    continue
                sprite.validate_size()

                file = sprite.file
                if file is not None:
                    file = file.value

                mask_file = sprite.mask_file
                if mask_file is not None:
                    mask_file = mask_file.value

                key = (file, mask_file)
                sprite_files.setdefault(key, []).append(sprite)

    # Check whether we can terminate sprite processing prematurely for
    #     dependency checks
    skip_sprite_processing = True
    for outputfile in outputfiles:
        if isinstance(outputfile, output_dep.OutputDEP):
            with outputfile:
                for f in sprite_files:
                    if f[0] is not None:
                        outputfile.write(f[0])
                    if f[1] is not None:
                        outputfile.write(f[1])
        skip_sprite_processing &= outputfile.skip_sprite_checks()

    if skip_sprite_processing:
        generic.clear_progress()
        return 0

    if not Image and len(sprite_files) > 0:
        generic.print_error("PIL (python-imaging) wasn't found, no support for using graphics")
        sys.exit(3)

    generic.print_progress("Checking palette of source images ...")

    used_palette = forced_palette
    last_file = None
    for f_pair in sprite_files:
        # Palette is defined by mask_file, if present. Otherwise by the main file.
        f = f_pair[1]
        if f is None:
            f = f_pair[0]

        try:
            with Image.open(generic.find_file(f)) as im:
                # Verify the image is running in Palette mode, if not, skip this file.
                if im.mode != "P":
                    continue
                pal = palette.validate_palette(im, f)
        except IOError as ex:
            raise generic.ImageError(str(ex), f)

        if forced_palette != "ANY" and pal != forced_palette and not (forced_palette == "DEFAULT" and pal == "LEGACY"):
            raise generic.ImageError(
                "Image has '{}' palette, but you forced the '{}' palette".format(pal, used_palette), f
            )

        if used_palette == "ANY":
            used_palette = pal
        elif pal != used_palette:
            if used_palette in ("LEGACY", "DEFAULT") and pal in ("LEGACY", "DEFAULT"):
                used_palette = "DEFAULT"
            else:
                raise generic.ImageError(
                    "Image has '{}' palette, but \"{}\" has the '{}' palette".format(pal, last_file, used_palette), f
                )
        last_file = f

    palette_bytes = {"LEGACY": "W", "DEFAULT": "D", "ANY": "A"}
    if used_palette in palette_bytes:
        grf.set_palette_used(palette_bytes[used_palette])
    encoder = None
    for outputfile in outputfiles:
        outputfile.palette = used_palette  # used by RecolourSpriteAction
        if isinstance(outputfile, output_grf.OutputGRF):
            if encoder is None:
                encoder = spriteencoder.SpriteEncoder(compress_grf, crop_sprites, used_palette)
            outputfile.encoder = encoder

    generic.clear_progress()

    # Read all image data, compress, and store in sprite cache
    if encoder is not None:
        encoder.open(sprite_files)

    # If there are any 32bpp sprites hint to openttd that we'd like a 32bpp blitter
    if alt_sprites.any_32bpp_sprites:
        grf.set_preferred_blitter("3")

    generic.print_progress("Linking actions ...")

    if action8_index != -1:
        actions = [sprite_count.SpriteCountAction(len(actions))] + actions

    for idx, action in enumerate(actions):
        num = start_sprite_num + idx
        action.prepare_output(num)

    # Processing finished, print some statistics
    action0.print_stats()
    actionF.print_stats()
    action7.print_stats()
    action1.print_stats()
    action2.print_stats()
    action6.print_stats()
    grf.print_stats()
    global_constants.print_stats()
    action4.print_stats()
    action11.print_stats()

    generic.print_progress("Writing output ...")

    md5 = None
    for outputfile in outputfiles:
        if isinstance(outputfile, output_grf.OutputGRF):
            outputfile.open()
            for action in actions:
                action.write(outputfile)
            outputfile.close()
            md5 = outputfile.get_md5()

        if isinstance(outputfile, output_nfo.OutputNFO):
            outputfile.open()
            for action in actions:
                action.write(outputfile)
            outputfile.close()

    if md5 is not None and md5_filename is not None:
        with open(md5_filename, "w", encoding="utf-8") as f:
            f.write(md5 + "\n")

    if encoder is not None:
        encoder.close()

    generic.clear_progress()
    return 0


def run():
    try:
        main(sys.argv[1:])

    except generic.ScriptError as ex:
        generic.print_error(str(ex))

        if developmode:
            raise  # Reraise exception in developmode
        sys.exit(1)

    except SystemExit:
        raise

    except KeyboardInterrupt:
        generic.print_error("Application forcibly terminated by user.")

        if developmode:
            raise  # Reraise exception in developmode

        sys.exit(1)

    except Exception as ex:  # Other/internal error.

        if developmode:
            raise  # Reraise exception in developmode

        # User mode: print user friendly error message.
        ex_msg = str(ex)
        if len(ex_msg) > 0:
            ex_msg = '"{}"'.format(ex_msg)

        traceback = sys.exc_info()[2]
        # Walk through the traceback object until we get to the point where the exception happened.
        while traceback.tb_next is not None:
            traceback = traceback.tb_next

        lineno = traceback.tb_lineno
        frame = traceback.tb_frame
        code = frame.f_code
        filename = code.co_filename
        name = code.co_name
        del traceback  # Required according to Python docs.

        ex_data = {
            "class": ex.__class__.__name__,
            "version": version,
            "msg": ex_msg,
            "cli": sys.argv,
            "loc": 'File "{}", line {:d}, in {}'.format(filename, lineno, name),
        }

        msg = (
            "nmlc: An internal error has occurred:\n"
            "nmlc-version: {version}\n"
            "Error:    ({class}) {msg}.\n"
            "Command:  {cli}\n"
            "Location: {loc}\n".format(**ex_data)
        )

        generic.print_error(msg)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    run()
