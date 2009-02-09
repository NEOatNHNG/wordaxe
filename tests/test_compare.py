#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from reportlab.lib.units import cm
from reportlab.lib import pagesizes
from reportlab.lib import enums
from reportlab.lib.colors import blue, red, black
import reportlab.lib.styles
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.flowables import KeepInFrame
from reportlab.pdfgen.canvas import Canvas

import wordaxe
import wordaxe.rl.styles
from wordaxe.DCWHyphenator import DCWHyphenator
from wordaxe.rl.paragraph import Paragraph as HyParagraph


__author__ = "Dinu Gherman"


wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)

    
stylesheet = wordaxe.rl.styles.getSampleStyleSheet()
st = stylesheet['Normal']
st.fontName = 'Helvetica'
st.fontSize = 10
st.leading = 12
st.spaceBefore = 1
st.spaceAfter = 4
st.alignment = enums.TA_LEFT

stylesheetHy = reportlab.lib.styles.getSampleStyleSheet()
sth = stylesheetHy['Normal']
sth.fontName = 'Helvetica'
sth.fontSize = 10
sth.leading = 12
sth.spaceBefore = 1
sth.spaceAfter = 4
sth.alignment = enums.TA_LEFT
sth.language = 'DE'
sth.hyphenation = True


testdata = u"<para>Sommer zweiundneunzig, also zweiundfünfzig Jahre nach Niederschreibung jener Jugendarbeit, saß ich in einer Sommerwohnung in Schlesien, den schönen Zug des Riesengebirges als Panorama vor mir. Eines Morgens traf »eingeschrieben« ein ziemlich umfangreiches Briefpaket ein, augenscheinlich ein Manuskript. Absender war ein alter Herr, der, zur Zeit als Pensionär in Görlitz lebend, in seinen besten Mannesjahren Bürgermeister in jener Stadt gewesen war, in deren Nähe die vorerzählte Tragödie gespielt und in deren Mauern die Prozeßverhandlung stattgefunden hatte. Während seiner Amtsführung war ihm die Lust gekommen, sich eingehender mit jener Cause célèbre zu beschäftigen, und was er mir da schickte, war das den Akten entnommene Material zu einem, wie er mit Recht meinte, »märkischen Roman«. In den Begleitzeilen hieß es: »Ich schicke Ihnen das alles; denn Sie sind der Mann dafür, und ich würde mich freun, den Stoff, der mir ein sehr guter zu sein scheint, durch Sie behandelt zu sehn.« (aus: Theodor Fontane, Von Zwanzig bis Dreißig)</para>"


class KifTestCase(unittest.TestCase):
    "Test inside KeepInFrame showing space gained by hyphenation."

    def test(self):    
        outPDF = "test_compare.pdf"
        pageSize = pagesizes.portrait(pagesizes.A4)
        canv = Canvas(outPDF, pagesize=pageSize)
    
        # common variables
        W, H = 5*cm, 20*cm
        kifMode = "shrink" # overflow/truncate/shrink/error
        
        # hyphenated column
        p = HyParagraph(testdata, sth)
        story = [p]
        frame = KeepInFrame(W, H, story, mode=kifMode)
        w, h = frame.wrapOn(canv, W, H)
        x, y = 100, 100
        frame.drawOn(canv, x, y+(H-h))
        canv.setLineWidth(2)
        canv.setStrokeColor(black)
        canv.circle(x, y, 10)
        canv.setStrokeColor(red)
        canv.rect(x, y, W, H)
        canv.setLineWidth(1)
        canv.setStrokeColor(blue)
        canv.rect(x, y+(H-h), w, h)
        
        # non-hyphenated column
        p = Paragraph(testdata, st)
        story = [p]
        frame = KeepInFrame(W, H, story, mode=kifMode)        
        w, h = frame.wrapOn(canv, W, H)
        x, y = 300, 100
        frame.drawOn(canv, x, y+(H-h))
        canv.setLineWidth(2)
        canv.setStrokeColor(black)
        canv.circle(x, y, 10)
        canv.setStrokeColor(red)
        canv.rect(x, y, W, H)
        canv.setLineWidth(1)
        canv.setStrokeColor(blue)
        canv.rect(x, y+(H-h), w, h)
    
        canv.showPage()
        canv.save() 


if __name__ == "__main__":
    unittest.main()
