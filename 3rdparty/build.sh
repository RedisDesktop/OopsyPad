#!/bin/bash

DIR=$(dirname "$(readlink -f "$0")")

function build_breakpad {
    cd $DIR/breakpad
    git clone https://chromium.googlesource.com/linux-syscall-support src/third_party/lss || true
    touch README
    ./configure
    make -s -j 2
}

function build_stackwalk {
    cd $DIR/minidump-stackwalk
    make
}

build_breakpad
build_stackwalk

cp $DIR/breakpad/src/processor/minidump_stackwalk $DIR/../oopsypad/bin/
cp $DIR/breakpad/src/tools/linux/dump_syms/dump_syms $DIR/../oopsypad/bin/
cp $DIR/minidump-stackwalk/stackwalker $DIR/../oopsypad/bin/
