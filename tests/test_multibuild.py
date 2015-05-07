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

import traceback

class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        #self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('normal', [Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm, id='F1')])
        self.addPageTemplates(template)
    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if flowable.__class__.__name__ == 'Paragraph':
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'Heading1':
                self.notify('TOCEntry', (0, text, self.page))
            if style == 'Heading2':
                self.notify('TOCEntry', (1, text, self.page))

class MultiBuildTestCase(unittest.TestCase):
    "Test muiltibuild"

    def test0(self):

        h1 = PS(name = 'Heading1',
            fontSize = 14,
            leading = 16)
        h2 = PS(name = 'Heading2',
            fontSize = 12,
            leading = 14,
            leftIndent = 2*cm)

        # Build story.
        story = []
        toc = TableOfContents()
        # For conciseness we use the same styles for headings and TOC entries
        toc.levelStyles = [h1, h2]
        story.append(toc)
        story.append(PageBreak())
        story.append(Paragraph('First heading', h1))
        story.append(Paragraph('Text in first heading', PS('body')))
        story.append(Paragraph('First sub heading', h2))
        story.append(Paragraph('Text in first sub heading', PS('body')))
        story.append(PageBreak())
        story.append(Paragraph('Second sub heading', h2))
        story.append(Paragraph('Text in second sub heading', PS('body')))
        story.append(Paragraph('Last heading', h1))
        doc = MyDocTemplate(outputfile('test_multibuild.pdf'))
        doc.multiBuild(story)

#noruntests
def makeSuite():
    return makeSuiteForClasses(MultiBuildTestCase)

#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()
