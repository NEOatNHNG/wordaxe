#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate

import wordaxe
import wordaxe.rl.styles
from wordaxe.DCWHyphenator import DCWHyphenator
from wordaxe.rl.paragraph import Paragraph

__author__ = "Dinu Gherman"


wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)


class KifTestCase(unittest.TestCase):
    "Test inside KeepInFrame showing space gained by hyphenation."

    def test(self):    
        stylesheetHy = getSampleStyleSheet()
        sth = stylesheetHy['Normal']
        sth.fontName = 'Helvetica'
        sth.fontSize = 32
        sth.leading = 36
        sth.language = 'DE'
        sth.hyphenation = True
    
        # von Hand getippt, 
        # geht mit und ohne Trennung (kein Zeilenumbruch)
        text = u"""<para>Ungefähr ein Jahr ist es her, </para>""".encode("utf8")
        
        # von Hand getippt, 
        # geht mit und ohne Trennung (Zeilenumbruch)
        # text = u"""<para>Ungefähr ein Jahr ist es her, dass CDU-Ministerpraesident</para>""".encode("utf8")
        
        # von Hand getippt, 
        # geht nur ohne Trennung (Zeilenumbruch plus Umlaut im Wort)
        # erzeugt bei Trennung Traceback [1]
        # text = u"""<para>Ungefähr ein Jahr ist es her, dass CDU-Ministerpräsident</para>""".encode("utf8")
        
        # von tagesschau.de kopiert und eingesetzt, 
        # geht ohne, aber nicht mit Trennung 
        # erzeugt bei Trennung gleichen Traceback [1]
        text = u"""<para>Ungefähr ein Jahr ist es her, dass CDU-Ministerpräsident Jürgen Rüttgers sich anschickte, die SPD links zu überholen. Denn auf seine Initiative hin beschlossen die Christdemokraten, die Bezugsdauer für ältere ALG-I-Empfänger zu Lasten von Jüngeren zu verlängern. So war das in der Berliner Koalition zwar nicht gedacht - aber Rüttgers setzte auf dem Parteitag von Dresden den Beschluss für eine längere Zahldauer trotzdem durch. Umgesetzt allerdings wurde der von der Großen Koalition nie.</para>""".encode("utf8")
        
        p = Paragraph(text, sth)
        story = [p]
        doc = SimpleDocTemplate("test_simple.pdf")
        doc.build(story)


if __name__ == "__main__":
    unittest.main()
