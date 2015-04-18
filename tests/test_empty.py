#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

from reportlab.lib.units import cm
from reportlab.lib import pagesizes
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import \
    Frame, Paragraph, PageTemplate, SimpleDocTemplate
from reportlab.platypus import Paragraph as NonHyphParagraph

__author__ = "Henning von Bargen"

"""
Test cases where the content of the paragraph is "empty".
"""

USE_HYPHENATION = True

if USE_HYPHENATION:
    try:
        import wordaxe.rl.styles
        from wordaxe.rl.paragraph import Paragraph
        from wordaxe.DCWHyphenator import DCWHyphenator
        wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
    except SyntaxError:
        print("could not import hyphenation - try to continue WITHOUT hyphenation!")


PAGESIZE = pagesizes.landscape(pagesizes.A4)

class EmptyContentTestCase(unittest.TestCase):
    "Test paragraphs with empty context."

    def testEmpty(self):
        "Generate a document with the given text"
        stylesheet = getSampleStyleSheet()
        normal = stylesheet['BodyText']
        normal.fontName = "Helvetica"
        normal.fontSize = 12
        normal.leading = 16
        normal.language = 'DE'
        normal.hyphenation = True
        story = []
        for text in [
            "",
            " ",
            "<para></para>",
            "<para> </para>",
            "&nbsp;",
            """<para><font backColor="red"> </font></para>"""
        ]:
            #print(repr(text))
            story.append(Paragraph("before", style=normal))
            story.append(Paragraph(text, style=normal))
            story.append(Paragraph("after", style=normal))
        doc = SimpleDocTemplate("test_empty.pdf", pagesize=PAGESIZE)
        doc.build(story)

if __name__ == "__main__":
    unittest.main()
