#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup


setup(
    name = "wordaxe",
    version = "0.2.5",
    description = "Provide hyphenation for python programs and ReportLab paragraphs.",
    long_description = "Provide hyphenation for python programs and ReportLab paragraphs.",
    author = "Henning von Bargen",
    author_email = "henning.vonbargen@arcor.de",
    maintainer = "Henning von Bargen",
    maintainer_email = "henning.vonbargen@arcor.de",
    license = "Apache License, version 2.0",
    platforms = ["Unix", "Windows"],
    keywords = ["multi-language", "hyphenation", "paragraphs", "reportlab"],
    url = "http://deco-cow.sourceforge.net",
    download_url = "http://sourceforge.net/project/showfiles.php?group_id=105867",
    packages = ["wordaxe", "wordaxe/rl"],
    package_data = {"wordaxe": ["dict/*.ini", "dict/*.dic"]},
)


# Backup original Reportlab's file rl_codecs.py -> rl_codecs.py.bak
# and replace the original with the one in hyphenation/rl if needed.

import sys, shutil, os.path, md5

def fileHash(path):
    "Return MD5 hash of an entire file."
    h = md5.new()
    h.update(open(path, "rb").read())
    return h.hexdigest()
    
setupCommand = sys.argv[-1]

if setupCommand == "install":
    from reportlab.pdfbase import rl_codecs
    src = rl_codecs.__file__
    if src.endswith(".pyc"):
        src = src[:-1]
    new = "wordaxe/rl/rl_codecs.py"
    if fileHash(src) != fileHash(new):
        bak = src + ".bak"
        print "backing up %s -> %s" % (src, bak)
        shutil.copy2(src, bak)
        print "copying %s -> %s" % (new, src)
        shutil.copy2(new, src)
    else:
        print "no update of '%s' needed" % src
