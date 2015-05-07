#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

__license__="""
   Copyright 2004-2008 Henning von Bargen (henning.vonbargen arcor.de)
   This software is dual-licenced under the Apache 2.0 and the
   2-clauses BSD license. For details, see license.txt
"""

__version__=''' $Id: __init__.py,v 1.2 2004/05/31 22:22:12 hvbargen Exp $ '''

__doc__="""Deutsche Anleitung zur Verwendung der wordaxe Silbentrennung
"""

from reportlab.lib.units import inch,cm,mm
from reportlab.lib import pagesizes
from reportlab.lib import enums
from reportlab.platypus.doctemplate import SimpleDocTemplate

from wordaxe.rl.styles import getSampleStyleSheet
from wordaxe.rl.paragraph import Paragraph
from wordaxe.rl.xpreformatted import XPreformatted

def myFirstPage(canvas, doc):
    canvas.saveState()
    canvas.restoreState()

def myLaterPages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "Seite %d" % doc.page)
    canvas.restoreState()

stylesheet=getSampleStyleSheet()
for name in ["Heading1", "Heading2", "Heading3", "Code", "BodyText"]:
    style = stylesheet[name]
    style.language = 'DE'
    style.hyphenation = True

import wordaxe
from wordaxe.plugins.PyHyphenHyphenator import PyHyphenHyphenator
wordaxe.hyphRegistry['DE'] = PyHyphenHyphenator('de_DE',5)

def makeParagraphs(txt,style):
    """Convert plain text into a list of paragraphs."""
    lines = txt.split("\n")
    retval = [Paragraph(line[:6]=='<para>' and line or ('<para>%s</para>' % line), style) for line in lines]
    return retval

doc = SimpleDocTemplate("test_pyhyphen.pdf",
                        title="wordaxe Anleitung (deutsch)",
                        author="Henning von Bargen",
                        pagesize=pagesizes.portrait(pagesizes.A4),
                        allowSplitting=1
                       )

# Content einlesen und parsen

content = open("dokumentation_de.txt", 'rb').read()

story = []
frags = []
opts = []

def emit(f, o):
    if len(f):
        if "PRE" in o:
            # Preformatted
            txt = "\n".join(f)
            story.append(XPreformatted(txt, stylesheet["Code"]))
        else:
            txt = " ".join([s.strip() for s in f])
            story.append(Paragraph(txt, stylesheet["BodyText"]))
    del o[:]
    del f[:]
    
for zeile in content.splitlines():
    # Dekodieren
    zeile = zeile.decode("iso-8859-1")
    zstrip = zeile.strip()
    # Überschrift?
    level = 0
    while zeile.startswith("=") and zeile.endswith("="):
        level += 1
        zeile = zeile[1:-1]
    if level > 0:
        emit(frags, opts)
        stil = "Heading%d" % level
        story.append(Paragraph(zeile, stylesheet[stil]))
    elif zstrip == "" and not "PRE" in opts:
        emit(frags, opts)
    elif zstrip == "{{{":
        emit(frags, opts)
        opts.append("PRE")
    elif zstrip == "}}}":
        emit(frags, opts)
    else:
        frags.append(zeile)

emit(frags, opts)
doc.build (story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)
