
for f in `ls -d *.txt docs docs/*.txt`; do cp -r $f dist; done

# Update Jenkins' NML
if [ "$USE_REV" == "tip" ] || [ "`hg id -r$USE_REV`" = "`hg id -rtip`" ] || [ "$BUILD_TYPE" == "releases"  ]; then
echo "Updating NML on main build node"
cd ~/bin/repos/nml-$BRANCH
hg pull -u
hg up -r$USE_REV
make extensions

echo "Updating NML on NewGRF build node"
# Update the default build machine (debian7, x64)
ssh repos@build-default << ENDSSH
cd nml-$BRANCH
hg pull
hg up -r${USE_REV}
make extensions
ENDSSH

else
echo "Neither tip nor a release was built. Not updating NML"
fi

