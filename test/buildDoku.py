#!/bin/env/python
# -*- coding: iso-8859-1 -*-

__license__="""
   Copyright 2004-2007 Henning von Bargen (henning.vonbargen arcor.de)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

__version__=''' buildDoku.py, V 1.0,  Henning von Bargen, $Revision:  1.0 '''

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
from wordaxe.DCWHyphenator import DCWHyphenator
wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE',5)

def makeParagraphs(txt,style):
    """Convert plain text into a list of paragraphs."""
    lines = txt.split("\n")
    retval = [Paragraph(line[:6]=='<para>' and line or ('<para>%s</para>' % line), style) for line in lines]
    return retval

doc = SimpleDocTemplate("dokumentation_de.pdf",
                        title="wordaxe Anleitung (deutsch)",
                        author="Henning von Bargen",
                        pagesize=pagesizes.portrait(pagesizes.A4),
                        allowSplitting=1
                       )

# Content einlesen und parsen

content = open("dokumentation_de.txt").read()

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
    # Umkodieren nach utf8
    zeile = zeile.decode("iso-8859-1").encode("utf8")
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
