#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest


__author__ = "Henning von Bargen"

if False:
    # We know that PyHnj does not hyphenate many German words as it should,
    # so leave this test out
    class WordlistTestCase(unittest.TestCase):
        "Test hyphenation using a word list with PyHnj."

        def i_test(self, hy):
            errs = []
            def error(msg, *args):
                errs.append(msg % args)
            hy.testWordList("test_wordlist.txt", "utf8", error)
            errors = "\n".join(errs)
            #self.assertEqual (errors, "")
            if errors:
                print("WordlistTestCase: The following words are not hyphenated as they should:")
                print(errors)

        def test(self):
            from wordaxe.PyHnjHyphenator import PyHnjHyphenator
            hnjHyphenator = PyHnjHyphenator('de_DE', 4, purePython=1)
            self.i_test(hnjHyphenator)


class DCWWordlistTestCase(unittest.TestCase):
    "Test hyphenation using a word list with DCW."

    def i_test(self, hy):
        errs = []
        def error(msg, *args):
            errs.append(msg % args)
        hy.testWordList("test_wordlist.txt", "utf8", error)
        errors = "\n".join(errs)
        #self.assertEqual (errors, "")
        if errors:
            print("DCWWordlistTestCase: The following words are not hyphenated as they should:")
            print(errors)

    def test(self):
        from wordaxe.DCWHyphenator import DCWHyphenator
        dcwHyphenator = DCWHyphenator('DE', 4)
        self.i_test(dcwHyphenator)

class PyHyphenWordlistTestCase(unittest.TestCase):
    "Test hyphenation using a word list with PyHyphen."

    def i_test(self, hy):
        errs = []
        def error(msg, *args):
            errs.append(msg % args)
        hy.testWordList("test_wordlist.txt", "utf8", error)
        errors = "\n".join(errs)
        #self.assertEqual (errors, "")
        if errors:
            print("PyHyphenWordlistTestCase: The following words are not hyphenated as they should:")
            print(errors)

    def test(self):
        from wordaxe.plugins.PyHyphenHyphenator import PyHyphenHyphenator
        hyphenator = PyHyphenHyphenator('de_DE', 4)
        self.i_test(hyphenator)

if __name__ == "__main__":
    unittest.main()
