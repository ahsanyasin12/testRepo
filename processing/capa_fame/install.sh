#!/bin/bash
SCRIPT=`realpath $0`
SCRIPTPATH=`dirname $SCRIPT`

TARGETDIR="$SCRIPTPATH/src/capa"
CAPA="https://github.com/fireeye/capa.git"
CAPARULES="https://github.com/fireeye/capa-rules.git"

GIT=$(which git)
PIP=$(which pip)

SUBMODULEPATH_OLD="git@github.com:fireeye"
SUBMODULEPATH_NEW="https://github.com/fireeye"

# init
[ ! -d "/path/to/dir" ] && mkdir -p $TARGETDIR

$GIT clone $CAPA $TARGETDIR
cd $TARGETDIR
sed -i "s#$SUBMODULEPATH_OLD#$SUBMODULEPATH_NEW#g" .gitmodules
$GIT submodule init
$GIT submodule update --remote rules

cd $SCRIPTPATH
$PIP install -qq -r $SCRIPTPATH/rsc/requirements.txt
