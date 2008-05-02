#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Runs all test files in current folder."""

import os
import sys
from os.path import join, splitext, basename
import glob
import unittest


def makeSuite(folder, pattern='test_*.py'):
    "Build a test suite of all available test files."

    if os.path.isdir(folder): 
        sys.path.insert(0, folder)
    
    testSuite = unittest.TestSuite()
    filenames = glob.glob(join(folder, pattern))
    modnames = [basename(splitext(fn)[0]) for fn in filenames]
    loader = unittest.TestLoader()
    for mn in modnames:
        mod = __import__(mn)
        testSuite.addTest(loader.loadTestsFromModule(mod))

    return testSuite


def main(pattern='test_*.py'):
    try:
        folder = os.path.dirname(__file__)
        assert folder
    except:
        folder = os.path.dirname(sys.argv[0]) or os.getcwd()
    testSuite = makeSuite(folder, pattern)
    unittest.TextTestRunner().run(testSuite)


if __name__ == '__main__':
    if "--clean" in sys.argv[1:]:
        for fn in glob.glob("*"):
            ew = fn.endswith
            if not ew("expected.pdf") and not ew(".py"):
                print "removing", fn
                os.remove(fn)
    else:
        main()
