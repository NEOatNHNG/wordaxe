#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

__license__="""
   Copyright 2004-2008 Henning von Bargen (henning.vonbargen arcor.de)
   This software is dual-licenced under the Apache 2.0 and the
   2-clauses BSD license. For details, see license.txt
"""

__version__=''' $Id: __init__.py,v 1.2 2004/05/31 22:22:12 hvbargen Exp $ '''

__doc__="""Test hyphenation support in the Paragraph class,
for paragraphs that don't contain any markup.
"""

import unittest

from reportlab.platypus import Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch,cm,mm
from reportlab.lib import colors
from reportlab.lib import pagesizes
from reportlab.lib import enums
from wordaxe.rl.styles import getSampleStyleSheet
from reportlab.platypus.tables import LongTable
from reportlab.platypus.doctemplate import SimpleDocTemplate

try:
    import wordaxe
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.DCWHyphenator import DCWHyphenator
    wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
except ImportError:
    print("could not import wordaxe - try to continue WITHOUT hyphenation!")


def myFirstPage(canvas, doc):
    canvas.saveState()
    canvas.restoreState()


def myLaterPages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "Seite %d" % doc.page)
    canvas.restoreState()


stylesheet=getSampleStyleSheet()

cellStyle = stylesheet['Normal']
cellStyle.fontName = 'Helvetica'
cellStyle.fontSize = 10
cellStyle.leading = 12
cellStyle.spaceBefore = 1
cellStyle.spaceAfter = 1
cellStyle.alignment = enums.TA_JUSTIFY # or: enums.TA_LEFT, whatever you want

### The next two lines are important for hyphenation
cellStyle.language = 'DE'
cellStyle.hyphenation = True


def makeParagraphs(txt,style):
    """Convert plain text into a list of paragraphs."""
    lines = txt.split("\n")
    retval = [Paragraph(line[:6]=='<para>' and line or ('<para>%s</para>' % line), style) for line in lines]
    return retval


def doLayout (title, data, colWidths, outPDF):
    """Create a tabular PDF file from the given data.
    """
    pagesize = pagesizes.portrait(pagesizes.A4)

    tablestyle = TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                             ('BOX', (0,0), (-1,-1), 1, colors.black),
                             ('BACKGROUND', (0,0), (-1,0), colors.orange),
                             ('INNERGRID', (0,1), (-1,-1), 0.5, colors.black),
                             ('LEFTPADDING', (0,0), (-1,-1), 3),
                             ('RIGHTPADDING', (0,0), (-1,-1), 3),
                            ])

    doc = SimpleDocTemplate(outPDF, title=title,pagesize=pagesize,allowSplitting=1)
    story = []
    
    header = ["%d mm" % w for w in colWidths]
    colWidths = [w*mm for w in colWidths]
    if sum(colWidths) > pagesize[0]:
        raise ValueError("Overall column width too wide!")

    tabContent = [header]
    for txt in data:
        row = []
        # Note: we have to create copies by calling makeParagraphs for each cell.
        # We cannot just create one Paragraph and reference it several times.
        for col in colWidths:
            row.append(makeParagraphs(txt,cellStyle))
        tabContent.append(row)
    table = LongTable(tabContent, colWidths=colWidths, style=tablestyle, repeatRows=1)
    story.append(table)
    doc.build(story,onFirstPage=myFirstPage,onLaterPages=myLaterPages)
    
    
class PlaintextTestCase(unittest.TestCase):
    "Testing hyphenation in a plain text paragraph (not containing markup)."

    def test(self):
        outPDF = "test_special_words.pdf"

        # Column widths in mm
        colWidths = [29,44,59,74]

        # Some test data in German.
        saetze = [(u"Urinstinkte " * 20).strip(),
                  (u"Analphabeten haben es schwer. Analphabetismus ist eine Krankheit. ") * 10,
                 ]
        testdata = [u'<para>%s</para>' % t for t in saetze]
        doLayout ("Hyphenation for plain text paragraphs", testdata, colWidths, outPDF)

if __name__ == "__main__":
    unittest.main()