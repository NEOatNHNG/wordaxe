#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

from reportlab.lib.units import cm
from reportlab.lib import pagesizes
from reportlab.lib import enums
from reportlab.lib.colors import blue, red, black, Color, HexColor
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import \
    Frame, Paragraph, PageTemplate, BaseDocTemplate, NextPageTemplate, PageBreak
from reportlab.platypus import Paragraph as NonHyphParagraph
from reportlab.pdfgen.canvas import Canvas

__author__ = "Dinu Gherman"


USE_HYPHENATION = True

if USE_HYPHENATION:
    try:
        import wordaxe.rl.styles
        from wordaxe.rl.paragraph import Paragraph
        from wordaxe.DCWHyphenator import DCWHyphenator
        wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
    except SyntaxError:
        print("could not import wordaxe - try to continue WITHOUT hyphenation!")


testdata = u"""<para>Die seit Juni 2006 wöchentlich im Internet abrufbaren Video-Podcasts mit Bundeskanzlerin Angela Merkel (CDU) haben bisher mehr als 550.000 Euro gekostet. Das hat laut dem Magazin Focus das Bundespresseamt auf Anfrage des FDP-Bundestagsabgeordneten Volker Wissing mitgeteilt. Ein Video-Podcast werde demnach für durchschnittlich knapp 10.800 Euro produziert. Im Juni 2006 war noch von 6500 Euro Kosten je Ausgabe die Rede. Jede Woche verzeichne das BPA etwa 200.000 Zugriffe auf Merkels Internet-Ansprachen, ein Zehntel davon Downloads auf Personalcomputer. (anw/c't)</para>"""

PAGESIZE = pagesizes.landscape(pagesizes.A4)


class TwoColumnDocTemplate(BaseDocTemplate):
    "Define a simple, two column document."

    def __init__(self, filename, **kw):
        m = 2*cm
        cw, ch = (PAGESIZE[0]-2*m)/2., (PAGESIZE[1]-2*m)
        f1 = Frame(m, m+0.5*cm, cw-0.75*cm, ch-1*cm, id='F1',
            leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
            showBoundary=True
        )
        f2 = Frame(cw+2.7*cm, m+0.5*cm, cw-0.75*cm, ch-1*cm, id='F2',
            leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
            showBoundary=True
        )
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('template', [f1, f2])
        self.addPageTemplates(template)


class FrameSwitchTestCase(unittest.TestCase):
    "Test hyphenation with switching frames."

    def test(self):
        stylesheet = getSampleStyleSheet()
        normal = stylesheet['BodyText']
        normal.fontName = "Helvetica"
        normal.fontSize = 12
        normal.leading = 16
        normal.language = 'DE'
        normal.hyphenation = True

        story = []
        if False:
            for i in range(3):
                p = Paragraph(testdata, style=normal)
                story.append(p)
        else:
            story.append(Paragraph(testdata*3, style=normal))
        doc = TwoColumnDocTemplate("test_frames.pdf", pagesize=PAGESIZE)
        doc.build(story)


if __name__ == "__main__":
    unittest.main()
