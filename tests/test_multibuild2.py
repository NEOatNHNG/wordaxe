#!/usr/bin/env python 
# -*- coding: UTF-8 -*-
#
#
# This test was contributed by Harald Armin Massa,
# I just modified the text generation code and made it a unittest.
# Many Thanks!

import unittest
from tests.utils import makeSuiteForClasses, outputfile, printLocation

import time
from io import BytesIO

from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4 
from reportlab.pdfgen.canvas import Canvas 
from reportlab.platypus.tables import Table, TableStyle
from reportlab.platypus import \
    PageBreak, FrameBreak, NextPageTemplate, Frame, Spacer, Paragraph,KeepTogether,BaseDocTemplate, \
    PageTemplate, Frame, KeepTogether, Paragraph
from reportlab.platypus.doctemplate import IndexingFlowable
from reportlab.lib.styles import ParagraphStyle, StyleSheet1 


try:
    import wordaxe.rl.styles
    from wordaxe.rl.paragraph import Paragraph as HyParagraph
    from wordaxe.DCWHyphenator import DCWHyphenator
    wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
    #~ wordaxe.hyphRegistry['DE'] =PyHnjHyphenator('DE',minWordLength=4,
                  #~ quality=8,
                  #~ hyphenDir=None,
                  #~ purePython=True)
    HAVE_WORDAXE = True
except:
    HAVE_WORDAXE = False
    raise
    if __name__ == "__main__":
        url = "http://deco-cow.wiki.sourceforge.net"
        print("Module 'wordaxe' not found. Continuing without hyphenation.")
        print("You can download 'wordaxe' from %s." % url)
#~ HAVE_WORDAXE = False

def getStyleSheet():
    "Return a stylesheet object."

    stylesheet = StyleSheet1()
    add = lambda **kwdict:stylesheet.add(ParagraphStyle(**kwdict))

    add(name = 'bed',fontName = 'Helvetica',
        fontSize = 8,leading = 9,
        bulletFontName = 'Helvetica',
        bulletFontSize = 8,firstLineIndent = 0,
        leftIndent = 1*cm,rightIndent = 0,
        spaceAfter = 5,alignment = TA_JUSTIFY,
    )

    add(name = 'bedh0',
        parent = stylesheet['bed'],
        fontName = 'Helvetica-Bold',
        bulletFontName = 'Helvetica-Bold',
        bulletFontSize = 10,
        fontSize = 10,
        leading = 14,
        spaceAfter = 8,
        alignment = TA_LEFT,
    )

    add(name = 'bedh1',
        parent = stylesheet['bed'],
        fontName = 'Helvetica-Bold',
        bulletFontName = 'Helvetica-Bold',
        bulletFontSize = 9,
        fontSize = 9,
        spaceBefore = 0.7*cm,
        alignment = TA_LEFT,
    )

    add(name = 'bedh2',
        parent = stylesheet['bed'],
        bulletFontName = 'Helvetica',
        bulletFontSize = 8,
        bulletIndent = 0*cm,
        firstLineIndent = 0*cm,
        rightIndent = 0,
    )

    add(name = 'bedh2a',parent = stylesheet['bedh2'],   rightIndent = 0.1,  )
    add(name = 'bedh3',parent = stylesheet['bed'],)
    add(name = 'bedh4',parent = stylesheet['bed'],)
    add(name = 'bedh5',parent = stylesheet['bed'],)
    add(name = 'bedt1',parent = stylesheet['bed'],)
    add(name = 'bedt2',parent = stylesheet['bed'],firstLineIndent = 0*cm,leftIndent = 1*cm,rightIndent = 0,)
    add(name = 'bedt3',parent = stylesheet['bed'],bulletIndent = 1.5*cm,firstLineIndent = 0*cm,leftIndent = 1.9*cm,
        rightIndent = 0,)
    add(name = 'bedt3a',parent = stylesheet['bedt3'],)
    add(name = 'toch',fontName = 'Helvetica',fontSize = 10,spaceAfter = 8,alignment = TA_LEFT,    )
    add(name = 'toc0',fontName = 'Helvetica-Bold',        fontSize = 10,        leading = 11,        spaceBefore=16)
    add(name = 'toc1',fontName = 'Helvetica',fontSize = 8,leading = 9,spaceBefore=16)
    add(name = 'toc2',fontName = 'Helvetica',fontSize = 8,leading = 9,leftIndent = 1.5*cm,)
    return stylesheet

class TableOfContents(IndexingFlowable):
    """This creates a formatted table of contents.

    It presumes a correct block of data is passed in.
    The data block contains a list of (level, text, pageNumber)
    triplets.  You can supply a paragraph style for each level
    (starting at zero).
    """

    def __init__(self):
        self.entries = []
        self.colWidths = []
        self.tableStyle =  TableStyle([
                               #~ ('GRID', (0,0), (-1,-1), 1, colors.black),
                                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                ])
        self._table = None
        self._entries = []
        self._lastEntries = []


    def beforeBuild(self):
        # keep track of the last run
        self._lastEntries = self._entries[:]
        self.clearEntries()


    def isIndexing(self):
        return True


    def isSatisfied(self):
        return (self._entries == self._lastEntries)
        

    def notify(self, kind, stuff):
        """The notification hook called to register all kinds of events.

        Here we are interested in 'TOCEntry' events only.
        """
        if kind == 'TOCEntry':
            self.addEntry(*stuff)


    def clearEntries(self):
        self._entries = []


    # def addEntry(self, level, chap, text, pageNum):
    def addEntry(self, *entry):
        """Adds one entry to the table of contents.

        This allows incremental buildup by a doctemplate.
        Requires that enough styles are defined."""

        level = entry[0]
        assert type(level) == int, "Level must be an integer"
        assert level < len(self.levelStyles), \
               "Table of contents must have a style defined " \
               "for paragraph level %d before you add an entry" % level

        self._entries.append(entry)


    def addEntries(self, listOfEntries):
        """Bulk creation of entries in the table of contents.

        If you knew the titles but not the page numbers, you could
        supply them to get sensible output on the first run."""

        for entry in listOfEntries:
            self.addEntry(*entry)


    def wrap(self, availWidth, availHeight):
        "All table properties should be known by now."

        chapwidth=1.4*cm
        self.colWidths = (chapwidth, (availWidth-chapwidth)*0.65, (availWidth-chapwidth)*0.15)

        # makes an internal table which does all the work.
        # we draw the LAST RUN's entries!  If there are
        # none, we make some dummy data to keep the table
        # from complaining
        if len(self._lastEntries) == 0:
            _tempEntries = [(0, 0, "Placeholder for table of contents", 0)]
        else:
            _tempEntries = self._lastEntries

        tableData = []
        for (level, chap, text, pageNum) in _tempEntries:
            leftColStyle = self.levelStyles[level]
            rightColStyle = ParagraphStyle(name='leftColLevel%d' % level,
                                           parent=leftColStyle,
                                           leftIndent=0,
                                           alignment=TA_RIGHT)
            chapPara = Paragraph(str(chap), leftColStyle)
            leftPara = Paragraph(text, leftColStyle)
            rightPara = Paragraph(str(pageNum), rightColStyle)
            tableData.append([chapPara, leftPara, rightPara])

        self._table = Table(tableData, 
            colWidths=self.colWidths, style=self.tableStyle,
            hAlign='LEFT'
            )

        w, h = self._table.wrapOn(self.canv, availWidth, availHeight)
        self.width, self.height = w, h

        return (w, h)


    def split(self, availWidth, availHeight):
        """At this stage we do not care about splitting the entries,
        we will just return a list of platypus tables.  Presumably the
        calling app has a pointer to the original TableOfContents object;
        Platypus just sees tables.
        """
        return self._table.splitOn(self.canv, availWidth, availHeight)


    def drawOn(self, canvas, x, y, _sW=0):
        """Don't do this at home!  The standard calls for implementing
        draw(); we are hooking this in order to delegate ALL the drawing
        work to the embedded table object.
        """
        self._table.drawOn(canvas, x, y, _sW)

spam = [
u"""Wer eine solche Sprache spricht und damit die natürliche Sensibilität vor die Wissenskritik stellt, handelt wider die rationale Bildungstradition.""",
u"""Das eine sag' ich dir, und das merk dir für's Leben: Die Tage vor den Ferien...""",
u"""Donaudampfschiffkapitäne tragen während ihrer Arbeitszeit meist Donaudampfschiffkapitänsmützen.""",
u"""Eigentlich ist es gegenüber den Donaudampfschiffkapitänen ungerecht, dass über sie ständig solche Witze gemacht werden.""",
u"""Die Steinlaus ist ein possierliches Tierchen.""",
u"""Um erfolgreich Computerprogramme zu entwickeln, hilft es, wenn man etwas verrückt ist.""",
u"""Es hilft aber noch wesentlich mehr, nicht vollkommen verrückt zu sein, sondern einen Rest vom gesunden Menschenverstand zurück zu behalten.""",
u"""Und hier noch einige wahllose zusammengestellte Wörter: Popocatepetl. Labskaus. Entschädigungspflicht. Eltern haften für ihre Kinder.""",
u"""Weitere wahllos und sinlos hingeschriebene Phrasen: Ey, Sahni! Basssolo! Ich trau mich nicht! Beeeeooow! Toll!""",
u"""Das Bundesgesundheitsministerium empfiehlt: Lachen ist gesund!""",
u"""Lange Wörter wie z.B. "Silbentrennungsverfahren" eignen sich hervorragend zum Testen von automatischen Silbentrennungsverfahren.""",
u"""Im Grunde genommen läuft es doch auf folgendes hinaus: Man weiß es nicht! Man steckt nicht drin!""",
u"""Die Messe ist gelesen! Der Keks ist gegessen!""",
u"""Das Leben ist eines der schwersten.""",
u"""Ich will kein Käfer sein! Nein! Nein! Nein! Ein Käfer kriegt nie einen Kuss und hat auch ziemlich kleine Ohren, und wenn ich schon ein Tier sein muss, dann wär' ich gern als Pferd geboren! Ein Pferd ist größer noch als Du, und man zertritt es nur mit Mühe. Es gibt auch Pferde, die machen "Muh" - doch diese Pferde nennt man Kühe.""",
]

blah = [
u"Blahphase",
u"Blubber",
u"Blubblub",
u"Fasel",
u"Bla",
u"Gebläh",
u"Unendlich unnütze Füllwörter",
]

vielspam = []
for x in blah:
    for y in spam:
        vielspam.append(x + u": " + y)

xele=[
    (u'ixxx',u"inhaltsverzeichnis"),
    (u'ixxx',u"bereich2spaltig"),
     ]

level = 0
for i, t in enumerate(vielspam):
    typ = "h"
    if i % 30 == 0:
        if level > 0: level -= 1
    elif i % 13 == 0:
        if level > 0: level -= 1
    elif i % 9 == 0:
        level += 1
    elif i % 5 == 0:
        pass
    else:
        typ = "text"
    if typ == "text":
        stil = u"bedt1"
    else:
        stil = u"bedh%d" % level
        t = u" ".join(t.split(u" ")[:10])
    xele.append((u'i%d' % i, stil, t))

def tuples2flowables(elemente, stylesheet):
    "Create a list of flowables from a list of element tuples."
    table = []
    story = []
    sa=story.append
    toc = TableOfContents()
    toc.levelStyles = [stylesheet['toc0'], stylesheet['toc1'], stylesheet['toc2']]
    
    for el in elemente:
        ID = el[0]
        art = el[1]
        try:
            content = el[2:]
        except IndexError:
            content = []

        # switch to new page template
        if art == "neuerbereich":
            sa(NextPageTemplate("rest"))
            sa(PageBreak())
            continue
        elif art == "seitenumbruch":
            sa(PageBreak())
            continue
        elif art == "inhaltsverzeichnis":
            sa(Paragraph("Inhaltsverzeichnis", style=stylesheet['toch']))
            sa(toc)
            continue
        elif art == "bereich2spaltig":
            sa(NextPageTemplate("bed"))
            sa(PageBreak())
            continue


        elif art in frozenset("bedh0 bedh1 bedh2 bedh2a bedh3 bedh4 bedh5 bedt3a".split()):
            chapNum = "1.0"
            bedtx=stylesheet[art]
            if HAVE_WORDAXE and art not in frozenset("bedh0 bedh1 bedh2".split()):
                P = HyParagraph
                bedtx.language = 'DE'
                bedtx.hyphenation = True
            else:
                P = Paragraph
            p = P(content[0], style=bedtx , bulletText=chapNum)
            #~ p = Paragraph(text, style=stylesheet[art], bulletText=chapNum)
            p.chapNum = chapNum
            p.gboxID=ID
            sa(p)
            
            if art in frozenset("bedh0 bedh1 bedh2".split()):
                # Register as TOC entries.
                level = int(art[-1])
                text = p.getPlainText()
                toc.addEntry(level, chapNum, text, None)


            
        
        elif art in frozenset(["bedt1","bedt2", "bedt5", "bedt7"]):
            bedtx=stylesheet[art]
            if HAVE_WORDAXE: 
                P = HyParagraph
                bedtx.language = 'DE'
                bedtx.hyphenation = True
            else:
                P = Paragraph
            p = P(content[0], style=bedtx )
            sa(p)
        elif art in frozenset (["bedt3","bedt6"]):
            sa(Paragraph(content[0], style=stylesheet[art] , bulletText=u"–"))
        
        elif art == "keeptogether": # die letzten x elemente zusammenhalten
            anzahl=-1*int(content[0])
            keept2=story[anzahl:]
            story=story[:anzahl]
            sa=story.append
            sa(KeepTogether(keept2))

        # STUFF UNTREATED YET
        else:
            sa(Paragraph("* %s"  %(art,), style=stylesheet['Heading2']))

            rest = el[1:]
            for rel in rest:
                if rel is None:
                    rel = "None"
                sa(Paragraph("* %s" % (rel,), style=stylesheet['BodyText']))
        
        # render previously assembled table, if present
        if table:
            sa(Table(table, tabColWidths[art],style=tablestyle[art],hAlign = tabalign.get(art,"CENTER")))
            table=None


    return story

class TheDocTemplate(BaseDocTemplate): 
    "Document template implementing the overall layout." 
    
    def __init__(self, filename, **kw): 
        BaseDocTemplate.__init__(self, filename, **kw)
        m = margin = 2*cm
        pageSize = A4 

        showBondary=False
        # cover page
        width, height = (pageSize[0]-2*m), (pageSize[1]-2*m-6.5*cm) 
        pad = 0.3*cm
        coverFrame = Frame(m, m, width, height,  
            leftPadding=pad, topPadding=pad, 
            rightPadding=pad, bottomPadding=pad, 
            id="coverFrame", showBoundary=showBondary
        ) 

        # regular page
        width, height = (pageSize[0]-2*m), (pageSize[1]-2*m)
        regularFrame = Frame(m, m, width, height-0.5*cm,  
            leftPadding=0, topPadding=0, 
            rightPadding=0, bottomPadding=0, 
            id="regularFrame", showBoundary=showBondary 
        ) 

        # two-col page
        width, height = (pageSize[0]-m), (pageSize[1]-m)
        leftFrame = Frame(m-0.5*cm, m, width/2.-1*cm, height-0.5*cm-m,  
            leftPadding=0, topPadding=0, 
            rightPadding=0, bottomPadding=0, 
            id="leftFrame", showBoundary=showBondary 
        ) 
        rightFrame = Frame((width)/2.+m-0.5*cm, m, width/2.-1*cm, height-0.5*cm-m,  
            leftPadding=0, topPadding=0, 
            rightPadding=0, bottomPadding=0, 
            id="rightFrame", showBoundary=showBondary 
        ) 

        PT = PageTemplate
        coverPage = PT("cover", [coverFrame], onPage=self.makeCoverHeader) 
        otherPages = PT("rest", [regularFrame], onPage=self.makeHeaderAndFooter) 
        twocolPages = PT("bed", [leftFrame, rightFrame], onPage=self.makeHeaderAndFooter) 
        self.addPageTemplates([coverPage, otherPages, twocolPages])
        

    def beforeDocument(self):
        pass


    def afterFlowable(self, flowable):
        "Registers TOC entries and makes outline entries."
        if flowable.__class__.__name__ == 'Paragraph':
            styleName = flowable.style.name
            if styleName in frozenset( "bedh0 bedh1 bedh2".split()) and hasattr(flowable,"chapNum"):
                # Register TOC entries.
                level = int(styleName[-1])
                chapNum = flowable.chapNum
                text = flowable.getPlainText()
                pageNum = self.page
                self.notify('TOCEntry', (level, chapNum, text, pageNum))

                # Add PDF outline entries.
                key = str(hash(flowable))
                c = self.canv
                c.bookmarkPage(key)
                c.addOutlineEntry(text, key, level=level, closed=0)


    
    def makeCoverHeader(self, canv, doc):
        pass
    
    def makeHeader(self, canv, doc):
        pass
    
    def makeHeaderAndFooter(self, canv, doc):
        "Draw header and footer."
        pass


def flowables2pdf(story, Layout):
    "Render a Platypus story into PDF and return its PDF code."
    
    f = BytesIO()
    doc = Layout(f).multiBuild(story)
    f.seek(0)
    #~ pdfCode = f.read()

    return f
    
class MultiBuildTestCase(unittest.TestCase):
    "Test muiltibuild"

    def test0(self):
        stylesheet = getStyleSheet()
        Layout = TheDocTemplate
        flowables = tuples2flowables(xele, stylesheet)
        pdfCode = flowables2pdf(flowables, Layout).read()
        open(outputfile('test_multibuild2.pdf'), "wb").write(pdfCode)


#noruntests
def makeSuite():
    return makeSuiteForClasses(MultiBuildTestCase)

#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()
