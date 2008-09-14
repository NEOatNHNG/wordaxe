#!/bin/env/python
# -*- coding: utf-8 -*-

import os
import sys
import unittest


__author__ = "Henning von Bargen"


class WordlistTestCase(unittest.TestCase):
    "Test hyphenation using a word list."

    def i_test(self, hy):
        errs = []
        def error(msg, *args):
            errs.append(msg % args)
        hy.testWordList("test_wordlist.txt", "utf8", error)
        errors = "\n".join(errs)
        self.assertEqual (errors, "")

    def test(self):
        from wordaxe.PyHnjHyphenator import PyHnjHyphenator
        hnjHyphenator = PyHnjHyphenator('de_DE', 4, purePython=1)
        self.i_test(hnjHyphenator)

        #from wordaxe.DCWHyphenator import DCWHyphenator
        #dcwHyphenator = DCWHyphenator('DE', 4)
        #self.i_test(dcwHyphenator)

if __name__ == "__main__":
    unittest.main()
