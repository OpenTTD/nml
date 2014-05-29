# Get revision data for filename

# Make sure we fail on failed regression tests
set -e

BRANCH="$BRANCH-"
if [ "$BRANCH" == "default-" ]; then BRANCH=""; fi
REV="v`~/bin/getdays2000`"
REV="$BRANCH$REV"
if [ "$BUILD_TYPE" == "releases" ]; then REV="$USE_REV"; fi

# Check regressions
make -j2 regression

# Create version file
./setup.py --version

mkdir -p build

# Create source bundle, also for use as it needs no compilation (it's python!)
# hg archive -r $USE_REV -t tgz build/nml-$REV-src.tgz
# Build windows version!
# In order to obtain the necessary wine environment do the following:
# - Get the Python 3.3 installer for windows (.msi) and install it
# - pip install Pillow and ply. It's mandatory to use pip and not easy_install
#   or other means. The resulting nmlc.exe would not include the required
#   submodules and would not work while the modules were installed using
#   easy_install!
wine "C:\\Python33\\pythonw.exe" "C:\\Python33\\Scripts\\cxfreeze" nmlc
cp $HOME/.wine/drive_c/windows/system32/python33.dll dist/
mv dist nmlc-exe && mkdir dist
cd nmlc-exe
zip ../dist/nml-$REV-windows-win32.zip *
cd ..

# Use easy_install to create packages
python3 setup.py bdist
python3 setup.py bdist_egg
python3 setup.py sdist

cd dist
for i in `ls *.tar.gz *.zip *.rpm *.egg`; do md5sum $i > $i.md5; done
cd ..

# Create the editor files
./gen_editor kate
./gen_editor notepadpp
mv *.xml dist

echo "Build date: `date --rfc-3339='seconds'`" > dist/release.txt
echo "Revision: `hg id -n`:`hg id`" >> dist/release.txt

