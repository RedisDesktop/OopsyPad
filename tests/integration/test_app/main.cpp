#include <QDir>
#include <QFileInfo>

#include "crashhandler.h"

int main(int argc, char *argv[])
{           
    QFileInfo appPath(QString::fromLocal8Bit(argv[0]));
    QString appDir(appPath.absoluteDir().path());
    QString crashReporterPath = QString("%1/crashreporter").arg(appDir.isEmpty() ? "." : appDir);
    CrashHandler::instance()->Init(QDir::homePath(), appDir, crashReporterPath);

    // crash
    delete reinterpret_cast<QDir*>(0xFEE1DEAD);

}
