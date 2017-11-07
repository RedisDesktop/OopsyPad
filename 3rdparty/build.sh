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
