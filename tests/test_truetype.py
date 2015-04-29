#Copyright ReportLab Europe Ltd. 2000-2004
#see license.txt for license details
#history http://www.reportlab.co.uk/cgi-bin/viewcvs.cgi/public/reportlab/trunk/reportlab/test/test_platypus_paragraphs.py
"""Tests for the reportlab.platypus.paragraphs module.
"""

import sys, os
from operator import truth

import unittest
from tests.utils import makeSuiteForClasses, outputfile, printLocation

from reportlab.platypus import PageBreak
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.units import cm
from reportlab.platypus.tableofcontents import TableOfContents
from wordaxe.rl.styles import getSampleStyleSheet, ParagraphStyle as PS
from wordaxe.rl.NewParagraph import Paragraph
from wordaxe.rl.NewParagraph import StyledWord
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont

import traceback

class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('normal', [Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm, id='F1')])
        self.addPageTemplates(template)

class TrueTypeTestCase(unittest.TestCase):
    "Test TrueType kerning"

    def test0(self):

        registerFont(TTFont('Arial', 'arial.ttf'))
        registerFont(TTFont('ArialBold', 'arialbd.ttf'))
        registerFont(TTFont('ArialItalic', 'ariali.ttf'))
        registerFont(TTFont('VeraBoldItalic', 'arialbi.ttf'))
    
        h1a = PS(name = 'Heading1',
            fontName = 'Arial',
            kerning = True,
            fontSize = 14,
            leading = 16)
        h2a = PS(name = 'Heading2',
            fontName = 'Arial',
            kerning = True,
            fontSize = 12,
            leading = 14,
            leftIndent = 2*cm)
        h1b = PS(name = 'Heading1',
            fontName = 'Arial',
            kerning = False,
            fontSize = 14,
            leading = 16)
        h2b = PS(name = 'Heading2',
            fontName = 'Arial',
            kerning = False,
            fontSize = 12,
            leading = 14,
            leftIndent = 2*cm)

        # Build story.
        story = []
        story.append(Paragraph('AV cables VA Maya Vase WM WA AW with Kerning', h1a))
        story.append(Paragraph('AV cables VA Maya Vase WM WA AW without', h1b))
        story.append(Paragraph('<a href="http://av-cables.txt">AV</a> cables VA Maya Vase WM WA AW with Kerning', h2a))
        story.append(Paragraph('<a href="http://av-cables.txt">AV</a> cables VA Maya Vase WM WA AW without', h2b))
        story.append(Paragraph('The first line uses kerning, the second one does not. The kerning information is taken from the TrueType kerning table', PS('body')))
        doc = MyDocTemplate(outputfile('test_truetype.pdf'))
        doc.multiBuild(story)

#noruntests
def makeSuite():
    return makeSuiteForClasses(TrueTypeTestCase)

#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()
