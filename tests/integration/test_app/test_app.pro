QT -= gui

CONFIG += c++11 console
CONFIG -= app_bundle

DEFINES += QT_DEPRECATED_WARNINGS

SOURCES += main.cpp\
	   crashhandler.cpp

HEADERS += crashhandler.h

# Breakpad
BREAKPADDIR = $$PWD/../../../3rdparty/breakpad/src
DEPENDPATH += $$BREAKPADDIR

INCLUDEPATH += $$BREAKPADDIR/

#breakpad app need debug info inside binaries
win32-msvc* {
    QMAKE_CXXFLAGS += /MP
    QMAKE_LFLAGS_RELEASE += /MAP
    QMAKE_CFLAGS_RELEASE += /Zi
    QMAKE_LFLAGS_RELEASE += /debug /opt:ref
} else {
    QMAKE_CXXFLAGS+=-g
    QMAKE_CFLAGS_RELEASE+=-g
}

win32* {
    win32-g++ {
        # Workaround for mingw
        QMAKE_LFLAGS_RELEASE=
    }

    HEADERS += $$BREAKPADDIR/common/windows/string_utils-inl.h
    HEADERS += $$BREAKPADDIR/common/windows/guid_string.h
    HEADERS += $$BREAKPADDIR/client/windows/handler/exception_handler.h
    HEADERS += $$BREAKPADDIR/client/windows/common/ipc_protocol.h
    HEADERS += $$BREAKPADDIR/google_breakpad/common/minidump_format.h
    HEADERS += $$BREAKPADDIR/google_breakpad/common/breakpad_types.h
    HEADERS += $$BREAKPADDIR/client/windows/crash_generation/crash_generation_client.h
    HEADERS += $$BREAKPADDIR/common/scoped_ptr.h
    SOURCES += $$BREAKPADDIR/client/windows/handler/exception_handler.cc
    SOURCES += $$BREAKPADDIR/common/windows/string_utils.cc
    SOURCES += $$BREAKPADDIR/common/windows/guid_string.cc
    SOURCES += $$BREAKPADDIR/client/windows/crash_generation/crash_generation_client.cc
}

unix:macx { # OSX
    PRE_TARGETDEPS += $$BREAKPADDIR/client/mac/build/Release/Breakpad.framework
    LIBS += $$BREAKPADDIR/client/mac/build/Release/Breakpad.framework/Versions/A/Breakpad
    LIBS += /System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation
    LIBS += /System/Library/Frameworks/CoreServices.framework/Versions/A/CoreServices
}

unix:!macx { # ubuntu & debian
    LIBS += $$BREAKPADDIR/client/linux/libbreakpad_client.a
}



