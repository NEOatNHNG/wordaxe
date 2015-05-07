#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Runs all test files in current folder."""
from __future__ import print_function

import os
import sys
from os.path import abspath, basename, dirname, isdir, join, splitext
import glob
import unittest

#we need to ensure 'tests' is on the path.  It will be if you
#run 'setup.py tests', but won't be if you CD into the tests
#directory and run this directly
testdir = dirname(abspath(__file__))
sys.path.insert(0, dirname(testdir))

from tests.utils import GlobDirectoryWalker, outputfile, printLocation


exclude = ('test_frames3f',)

keep = ('.py', '.gif', '.png', 'expected.pdf',
    'test_wordlist.txt', 'special_words.lst',
    'dokumentation_de.txt', 'dokumentation_en.txt')


def makeSuite(folder, pattern='test_*.py'):
    """Build a test suite of all available test files."""

    if isdir(folder): 
        sys.path.insert(0, folder)

    testSuite = unittest.TestSuite()
    filenames = glob.glob(join(folder, pattern))
    modnames = [basename(splitext(fn)[0]) for fn in filenames]
    loader = unittest.TestLoader()
    for mn in modnames:
        if mn in exclude:
            continue
        mod = __import__(mn)
        testSuite.addTest(loader.loadTestsFromModule(mod))

    return testSuite


def main(pattern='test_*.py'):
    try:
        folder = dirname(__file__)
        assert folder
    except:
        folder = dirname(sys.argv[0]) or os.getcwd()
    testSuite = makeSuite(folder, pattern)
    unittest.TextTestRunner().run(testSuite)


def clean():
    os.chdir(testdir)
    for fn in glob.glob("*"):
        ew = fn.endswith
        for n in keep:
            if fn.endswith(n):
                break
        else:
            print("removing", fn)
            os.remove(fn)


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--clean' in args:
        clean()
    else:
        try:
            pattern = args[0]
        except IndexError:
            pattern = 'test_*.py'
        main(pattern)
