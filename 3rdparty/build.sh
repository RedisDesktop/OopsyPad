#!/bin/bash

# On OSX use coreutils package to fix absense of readlink command
if [[ $OSTYPE == darwin* ]]; then
  brew install coreutils || true
  PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH"
fi

DIR=$(dirname "$(readlink -f "$0")")

function build_breakpad {

    cd $DIR/breakpad
    touch README   
    
    # NOTE(u_glide): Only client-mode is supported on OSX
    if [[ $OSTYPE == darwin* ]]; then
        xcodebuild -sdk macosx -project src/tools/mac/dump_syms/dump_syms.xcodeproj -configuration Release ARCHS=x86_64               
    else
        git clone https://chromium.googlesource.com/linux-syscall-support src/third_party/lss || true            
        ./configure
        make -s -j 2
    fi
}

function build_stackwalk {
    cd $DIR/minidump-stackwalk
    make
}

# NOTE(u_glide): Only client-mode is supported on OSX
if [[ $OSTYPE == darwin* ]]; then
    build_breakpad
    cp $DIR/breakpad/src/tools/mac/dump_syms/build/Release/dump_syms $DIR/../oopsypad/bin/
else
    build_breakpad
    build_stackwalk
    cp $DIR/breakpad/src/tools/linux/dump_syms/dump_syms $DIR/../oopsypad/bin/
    cp $DIR/breakpad/src/processor/minidump_stackwalk $DIR/../oopsypad/bin/
    cp $DIR/minidump-stackwalk/stackwalker $DIR/../oopsypad/bin/
fi
