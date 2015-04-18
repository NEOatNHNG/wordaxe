#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import unittest

import traceback

__author__ = "Henning von Bargen"

from wordaxe import *

OUTPUT = False

words = u"""
raven\u2019s
Dr.\u00A0Who
""".splitlines()

def test_words(hyphenator):
    if OUTPUT: print("Testing", hyphenator, "...")
    errors = []
    for word in words:
        if word:
            try:
                hword = u"n/a"
                hword = hyphenator.hyphenate(word)
                assert hword is None or isinstance(hword, HyphenatedWord)
                if OUTPUT: print((u"word:%s result:%s" % (word, hword)).encode("ascii", "xmlcharrefreplace"))
            except:
                errors.append(u"word:%s result:%s exception:%s" %
                              (word, hword, traceback.format_exc()))
    if errors:
        raise AssertionError("Errors for %r:\n" % hyphenator + "\n".join([e.encode("ascii","backslashreplace") for e in errors]))


if False:
    # We know that PyHnj does not hyphenate many German words as it should,
    # so leave this test out
    class WordlistTestCase(unittest.TestCase):
        "Test hyphenation using a word list with PyHnj."

        def test(self):
            from wordaxe.PyHnjHyphenator import PyHnjHyphenator
            hyphenator = PyHnjHyphenator('de_DE', 4, purePython=1)
            test_words(hyphenator)


class DCWWordlistTestCase(unittest.TestCase):
    "Test hyphenation using a word list with DCW."

    def test(self):
        from wordaxe.DCWHyphenator import DCWHyphenator
        hyphenator = DCWHyphenator('DE', 4)
        test_words(hyphenator)

class PyHyphenWordlistTestCase(unittest.TestCase):
    "Test hyphenation using a word list with PyHyphen."

    def test(self):
        from wordaxe.plugins.PyHyphenHyphenator import PyHyphenHyphenator
        hyphenator = PyHyphenHyphenator('de_DE', 4)
        test_words(hyphenator)

if __name__ == "__main__":
    OUTPUT = True
    unittest.main()
