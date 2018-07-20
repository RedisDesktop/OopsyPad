#!/bin/bash

DIR=$(dirname "$(readlink -f "$0")")

function build_breakpad {

    cd $DIR/breakpad
    touch README   
    
    # NOTE(u_glide): Only client-mode is supported on OSX
    if [[ $OSTYPE == darwin* ]]; then
        wget "https://02692989752462866653.googlegroups.com/attach/75865a958e446/dump_syms.patch?part=0.1&view=1&vt=ANaJVrE_51_bXadOKL5j07yqsuBjehkaBp20gX6b1WUQsRv4xpPJl02wUkUwypXr9JfpkUYrAgEnDzZ3rmLUdIj6Xryxb9kY4gL6kd0gVYxRSd-2rvAd-dE" -O dump_syms.patch
        git apply dump_syms.patch
        xcodebuild -quiet -sdk macosx -project src/tools/mac/dump_syms/dump_syms.xcodeproj -configuration Release ARCHS=x86_64               
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
    cd $DIR/breakpad/src/tools/mac/dump_syms/build/Release $DIR/../oopsypad/bin/
else
    build_breakpad
    build_stackwalk
    cp $DIR/breakpad/src/tools/linux/dump_syms/dump_syms $DIR/../oopsypad/bin/
    cp $DIR/breakpad/src/processor/minidump_stackwalk $DIR/../oopsypad/bin/
    cp $DIR/minidump-stackwalk/stackwalker $DIR/../oopsypad/bin/
fi
