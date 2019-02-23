
for f in $(ls -d README.md LICENSE *.txt docs docs/*.txt); do cp -r $f dist; done

# Update Jenkins' NML
if [ "$USE_REV" == "HEAD" ] || [ "$BUILD_TYPE" == "releases"  ] || [ "USE_REV" == "origin/master" ]; then
    echo "Updating NML-$BRANCH on main build node"

    if [ ! -d "~/bin/repos/nml-$BRANCH" ]; then
        # Copy checkout of master to create a checkout for the non-existing branch
        cp -r ~/bin/repos/nml-master ~/bin/repos/nml-$BRANCH
    fi

    cd ~/bin/repos/nml-$BRANCH
    if [ "USE_REV" == "HEAD" ]; then
        git pull origin $BRANCH
    else
        git fetch origin
        git reset --hard $USE_REV
    fi

    # Build also the C-extensions
    make extensions

else
    echo "Neither tip nor a release was built. Not updating NML"
fi

