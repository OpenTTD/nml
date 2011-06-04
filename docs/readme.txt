NML readme
Last updated:    2011-06-04
Release version: 0.1.0
------------------------------------------------------------------------


Table of Contents:
------------------
1) About
2) Contact
3) Dependencies
3.1) Required dependencies
3.2) Optional dependencies
4) Installation
5) Usage
6) Known issues
7) Credits


1) About:
-- ------
NML is a a python-based compiler, capable of compiling NML files (along
with their associated language, sound and graphic files) into grf
and / or nfo files.

The documentation about the language can be found on
http://hg.openttdcoop.org/nml/raw-file/tip/docs/index.html

NML is licensed under the GNU General Public License version 2, or at
your option, any later version. For more information, see 'license.txt'
(GPL version 2), or later versions at <http://www.gnu.org/licenses/>.


2) Contact:
-- --------
Contact can be made via the issue tracker / source repository at
http://dev.openttdcoop.org/projects/nml or via IRC on the
#openttdcoop.devzone channel on OFTC.


3) Dependencies:
-- -------------

3.1) Required dependencies:
---- ----------------------
NML requires the following 3rd party packages to run:
 - python
     Minimal version is 2.5. Python 3 is not yet supported.
 - python image library
     downloadable from http://www.pythonware.com/products/pil/
 - ply
     downloadable from http://www.dabeaz.com/ply/

3.2) Optional dependencies:
---- ----------------------
To install NML you'll need these 3rd party packages:
 - buildout
     Only necesary if you want to use the installer. You can
     run NML without installation or manually install it.


4) Installation:
-- -------------
NML uses buildout for packaging / installation. To install NML run:
python setup.py install

If you want to install the package manually copy 'nmlc' to any directory
in your path and the directory 'nml' to any directory in your python path.


5) Usage:
-- ------
Usage: nmlc [options] <filename>
Where <filename> is the nml file to parse

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d, --debug           write the AST to stdout
  -s, --stack           Dump stack when an error occurs
  --grf=<file>          write the resulting grf to <file>
  --nfo=<file>          write nfo output to <file>
  -c                    crop extraneous transparent blue from real sprites
  -u                    save uncompressed data in the grf file
  --nml=<file>          write optimized nml to <file>
  -o <file>, --output=<file>
                        write output(nfo/grf) to <file>
  -t <file>, --custom-tags=<file>
                        Load custom tags from <file> [default:
                        custom_tags.txt]
  -l <dir>, --lang-dir=<dir>
                        Load language files from directory <dir> [default:
                        lang]
  -a <dir>, --sprites-dir=<dir>
                        Store 32bpp sprites in directory <dir> [default:
                        sprites]
  --default-lang=<file>
                        The default language is stored in <file> [default:
                        english.lng]
  --start-sprite=<num>  Set the first sprite number to write (do not use
                        except when you output nfo that you want to include in
                        other files)
  -p <palette>, --palette=<palette>
                        Force nml to use the palette <pal> [default: ANY].
                        Valid values are 'DOS', 'WIN', 'ANY'


6) Known issues:
-- -------------
See the issue tracker at https://dev.openttdcoop.org/projects/nml/issues


7) Credits:
-- --------
Active developers (in alphabetical order):
  Jasper Reichardt (Hirundo)
  Ingo von Borstel (planetmaker)
  José Soler (Terkhen)
  Thijs Marinussen (Yexo)

Inactive developers:
  Albert Hofkamp (Alberth)

Special thanks to:
  Richard Barrell
    For writing the buildout script needed to install NML.
