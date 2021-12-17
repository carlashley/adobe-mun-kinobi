#!/bin/zsh

PYTHON_SHEBANG="/usr/bin/env python3"
PKGROOT=./dist/pkgroot/usr/local/bin
PROJECT=adobe-mun-kinobi

if [ ! -d ${PKGROOT} ]; then
    /bin/mkdir -p ${PKGROOT}
fi

python3 -m zipapp src --compress --output ${PKGROOT}/${PROJECT} --python="${PYTHON_SHEBANG}"
