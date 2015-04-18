#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

from reportlab.lib.units import cm
from reportlab.lib import pagesizes
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import \
    Frame, Paragraph, PageTemplate, BaseDocTemplate
from reportlab.platypus import Paragraph as NonHyphParagraph

__author__ = "Dinu Gherman"


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


class TwoColumnDocTemplate(BaseDocTemplate):
    "Define a simple, two column document."
    
    def __init__(self, filename, **kw):
        m = 2*cm
        cw, ch = (PAGESIZE[0]-2*m)/2., (PAGESIZE[1]-2*m)
        
        # if we replace the value 4.9 with 5.0, everything works as expected
        f1 = Frame(m, m+0.5*cm, cw+4.9*cm, ch-1*cm, id='F1', 
            leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
            showBoundary=True
        )
        f2 = Frame(cw+7*cm, m+0.5*cm, cw-5*cm, ch-1*cm, id='F2', 
            leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
            showBoundary=True
        )
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('template', [f1, f2])
        self.addPageTemplates(template)


class Issue2901112TestCase(unittest.TestCase):
    """
    If a paragraph line ending with <br />
    does not fit without squeezing, then
    the height calculation is wrong (as if
    the paragraph contained one more line).
    """

    def test(self):    
        stylesheet = getSampleStyleSheet()
        normal = stylesheet['BodyText']
        normal.fontName = "Helvetica"
        normal.fontSize = 12
        normal.leading = 16
        normal.language = 'DE'
        normal.hyphenation = True
        normal.borderWidth = 1
        normal.borderColor = "red"
        story = []
    
        text = """<i><font size="10">XX bottles of beer on the wall, XX bottles of beer!</font></i><br />If one of those bottles should happen to be drunken, there'll be XX-1 bottles of beer on the wall!<br />XX bottles of beer on the wall, XX bottles of beer!<br />If one of those bottles should happen to be drunken, there'll be XX-1 bottles of beer on the wall!<br /><b>No more bottles of beer on the wall!</b> <font color="white" size="6">999999</font>"""
        story.append(Paragraph(text, style=normal))

        text = """<i><font size="10">XX bottles of beer on the wall, XX bottles of beer!</font></i><br />If one of those bottles should happen to be drunken, there'll be XX-1 bottles of beer on the wall!<br />XX bottles of beer on the wall, XX bottles of beer!<br />If one of those bottles should happen to be drunken, there'll be XX-1 bottles of beer on the wall! <b>No more bottles of beer on the wall!</b> <font color="white" size="6">999999</font>"""
        story.append(Paragraph(text, style=normal))
        
        story.append(Paragraph("The red border around the paragraphs above should end right below the text without additional space.", style=normal))

        doc = TwoColumnDocTemplate("test_issue2901112.pdf", pagesize=PAGESIZE)
        doc.build(story)


if __name__ == "__main__":
    unittest.main()
