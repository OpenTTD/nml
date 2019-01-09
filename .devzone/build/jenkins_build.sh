# Get revision data for filename

# Make sure we fail on failed regression tests
set -e

# Use the revision we're asked to build:
if [ "USE_REV" != "HEAD" ]; then
    git checkout $USE_REV
else
    git checkout $BRANCH
fi

VSTRING="$(python3 nml/version_info.py)"
HASH="$(echo $VSTRING | cut -d\; -f1)"
BRANCH="$(echo $VSTRING | cut -d\; -f2)"
TAG="$(echo $VSTRING | cut -d\; -f3)"
MODIFIED="$(echo $VSTRING | cut -d\; -f4)"
DATE="$(echo $VSTRING | cut -d\; -f5)"
REV="$(echo $VSTRING | cut -d\; -f6)"

# Check regressions
make -j1 regression

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
wine "C:\\Python33\\pythonw.exe" setup.py build -c mingw32
cp build/lib.win32-3.3/*.pyd dist/
mv dist nmlc-exe && mkdir dist
cd nmlc-exe
zip ../dist/nml-$REV-windows-win32.zip *
cd ..

# Use easy_install to create packages
python3 setup.py bdist
python3 setup.py bdist_egg
python3 setup.py sdist

cd dist
for i in *.tar.gz *.zip *.rpm *.egg; do md5sum $i > $i.md5; done
cd ..

# Create the editor files
./gen_editor kate
./gen_editor notepadpp
mv *.xml dist

echo "Build date: $DATE"        > dist/release.txt
echo "Revision: $BRANCH-$HASH" >> dist/release.txt
echo "Tag: $TAG"               >> dist/release.txt
echo "Modified: $MODIFIED"     >> dist/release.txt

