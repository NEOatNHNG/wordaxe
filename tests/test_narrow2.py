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

USE_HYPHENATION = True

if USE_HYPHENATION:
    try:
        import wordaxe.rl.styles
        from wordaxe.rl.paragraph import Paragraph
        from wordaxe.DCWHyphenator import DCWHyphenator
        wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
    except SyntaxError:
        import traceback
        traceback.print_exc()
        print("could not import hyphenation - try to continue WITHOUT hyphenation!")


PAGESIZE = pagesizes.landscape(pagesizes.A4)


class TwoColumnDocTemplate(BaseDocTemplate):
    "Define a simple, two column document."
    
    def __init__(self, filename, **kw):
        m = 2*cm
        cw, ch = (PAGESIZE[0]-2*m)/2., (PAGESIZE[1]-2*m)
        f1 = Frame(m, m+0.5*cm, 0.2*cm, ch-1*cm, id='F1', 
            leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
            showBoundary=True
        )
        f2 = Frame(cw+2.7*cm, m+0.5*cm, 0.3*cm, ch-1*cm, id='F2', 
            leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
            showBoundary=True
        )
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('template', [f1, f2])
        self.addPageTemplates(template)


class FrameSwitchTestCase(unittest.TestCase):
    "Test hyphenation with switching frames and font-tags in paragraphs."

    def test(self):    
        stylesheet = getSampleStyleSheet()
        normal = stylesheet['BodyText']
        normal.fontName = "Helvetica"
        normal.fontSize = 12
        normal.leading = 16
        normal.language = 'DE'
        normal.hyphenation = True
    
        text = "Wordaxe"
        story = []
        story.append(Paragraph(text, style=normal))
        story.append(Paragraph('<font color="red">%s</font>' % text, style=normal))
        doc = TwoColumnDocTemplate("test_narrow2.pdf", pagesize=PAGESIZE)
        doc.build(story)


if __name__ == "__main__":
    unittest.main()
