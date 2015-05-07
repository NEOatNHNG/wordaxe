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
        outPDF = "test_plain.pdf"

        # Column widths in mm
        colWidths = [29,44,59,74]

        # Some test data in German.
        testdata = ['<para>%s</para>' % t for t in
        [u"""Die nachfolgenden S\xE4tze sind \xFCbrigens nach M\xF6glichkeit v\xF6llig sinnlos. Sie enthalten aber teilweise besonders sch\xF6n lange zusammengesetzte W\xF6rter, damit der Silbentrennungsalgorithmus auch tats\xE4chlich sichtbar \xFCberpr\xFCft werden kann.""",
         u"""Kapit\xE4ns\xADm\xFCtzen\xADschirm\xADband""",
         u"""Das ist ein kurzer Satz""",
         u"""Hier kommt schon ein etwas l\xE4ngerer Satz""",
         u"""So, jetzt kommt endlich mal ein wirklich langer Satz, damit das Silbentrennungsverfahren tats\xE4chlich angewendet werden kann.""",
         u"""Der Bundeskanzler arbeitet im Bundeskanzleramt.""",
         u"""Daf\xFCr ist nicht das Bundesarbeitsgericht zust\xE4ndig, ebensowenig wie das Bundesverwaltungsgericht oder der Bundesverwaltungsgerichtsvorsteher.""",
         u"""Totaler bl\xF6dsinnabsoluternonsensundohnesinnundverstand""",
         u"""SCHWAMMSCHLACHT oder SCHLAMMSCHLACHT""",
         u"""Mit Silbentrennungsverfahren werden extrem lange W\xF6rter, die im deutschen Sprachgebrauch allt\xE4glich sind, automatisch in kleinere Bestandteile zerlegt, wobei die Lesbarkeit nach M\xF6glichkeit erhalten bleiben sollte.""",
         u"""Die schwarze Hand. Seit mehr als 170 Jahren wird auf dem Schloss Hohenlimburg eine abgetrennte rechte Menschenhand aufbewahrt und heute den BesucherInnen im dortigen Museum gezeigt.""",
         u"""Der \xFCberlieferung nach soll es sich um die Hand eines Edelknaben handeln, der h\xE4ufig seine Mutter geschlagen hatte. Sein Vater soll ihm daraufhin zur Strafe die Hand abgeschlagen haben. Diese Geschichte stellt seit Generationen ein Erziehungsmittel f\xFCr Kinder dar. Noch heute wird die Sage von der Schwarzen Hand jungen MuseumsbesucherInnen von ihren Eltern als abschreckendes Beispiel erz\xE4hlt.""",
         u"""Die Hand wurde wahrscheinlich um 1811 im mittelalterlichen Bergfried der Hohenlimburg gefunden. Ein Blitzschlag hatte den Turm getroffen und die oberen Stockwerke zerst\xF6rt. Hier befand sich das Archiv der Grafschaft Limburg, das 1840 in das Schloss Rheda verlagert wurde.""",
         u"""Die schwarze Einf\xE4rbung der Hand ist auf Brandeinwirkung zur\xFCckzuf\xFChren. Unter der verbrannten Oberfl\xE4che sind Spuren einer Mumifizierung zu sehen. Die Handwurzel zeigt Schnittspuren. Der kleine Finger soll nach einer \xFCberlieferung durch spielende Kinder abgebrochen worden sein.""",
         u"""Abgetrennte H\xE4nde wie die in Hohenlimburg sind keine Seltenheit. Sie dokumentieren die mittelalterliche Rechtsordnung und sind wahrscheinlich als sogennannte Leibzeichen anzusprechen, die beispielsweise Mordopfern als Tatbeweis abgetrennt wurden.""",
         u"""Unter hohenlimburg.de wird in Zusammenarbeit mit Prof. Dr. Gerhard E. Sollbach und Dr. Stephanie Marra M.A., Universit\xE4t Dortmund / Ruhr-Universit\xE4t Bochum, sowie anderen Fachwissenschaftlern ein Online-Portal zur Geschichte der mittelalterlichen Burganlage und fr\xFChneuzeitlichen Ortschaft sowie zu der bis 1807 autonomen Grafschaft Limburg vorbereitet. Grafschaft und Gemeinde Limburg k\xF6nnen auf eine reiche und vielf\xE4ltige Geschichte zur\xFCckblicken, die bis ins Hochmittelalter zur\xFCckreicht.""",
         u"""Die Hohenlimburger Geschichte ist spannend und lehrreich zugleich. Im Gegensatz zur heutigen Gro\xDFstadt Hagen, deren mittelalterliche Geschichte kaum nachvollziehbar ist, war die Grafschaft Limburg seit dem 13. Jahrhundert ein f\xFCr die rheinisch-westf\xE4lische Landesgeschichte bedeutendes Territorium.""",
         u"""Auf dem Hohenlimburger Geschichtsportal sollen auch die vornehmlich von Hobby-Historikern und Heimatforschern bis in die heutige Zeit tradierten Spekulationen, Deutungen, Legenden und Mythen der "Lokalgeschichte" kritisch hinterfragt und ihr tats\xE4chlicher historischer Wahrheitsgehalt wissenschaftlich nachpr\xFCfbar und allgemeinverst\xE4ndlich dargestellt werden. Diese Spekulationen halten sich hartn\xE4ckig und geh\xF6ren zu den zentralen Aussagen der Heimatforschung. Wann wurde Hohenlimburg tats\xE4chlich zur Stadt erhoben - bereits 1709 oder erst 1903?""",
         u"""Gab es 1252 wirklich ein "Marktrecht" f\xFCr eine mittelalterliche Ortschaft "Hohenlimburg"? Genau wie in Hagen, wo eine vermeintlich karolingische "Urpfarre" und ein vorgebliches "Hansequartier" die Heimatforschung befl\xFCgelten, so war auch in Hohenlimburg oft der Wunsch der Vater des Gedankens. Die Geschichte der Region ist jedoch auch ohne Legenden und Spektulationen eine sehr spannende und dabei vor allem durch historische Fakten abgesicherte "Reise in die Vergangenheit".""",
         u"""Die folgenden Texte sind Ausschnitte aus der Online-Hilfe von Windows XP.""",
         u"""Computer\xFCbergreifende Spiele. \xFCber Netzwerkverbindungen und eine gemeinsame Internetverbindung k\xF6nnen Familienmitglieder auf verschiedenen Computern sowohl miteinander als auch \xFCber das Internet spielen. W\xE4hrend des Spielens k\xF6nnen Sie dann au\xDFerdem im Internet surfen, z. B. um Ihre bevorzugten B\xF6rsen- oder Sportwebsites zu besuchen.""",
         u"""Windows XP umfasst viele neue Features, verbesserte Programme und Tools. Lernen Sie die Neuheiten kennen, und verschaffen Sie sich einen \xFCberblick \xFCber die im Lieferumfang von Windows XP enthaltenen Programme, Systeme, das Zubeh\xF6r sowie Kommunikations- und Unterhaltungsprogramme. Lesen Sie die entsprechenden Artikel mit umfassenden Beschreibungen zum Durchf\xFChren von wichtigen Aufgaben, vom Starten bis zum Beenden des Systems. Schlagen Sie unbekannte Begriffe im Glossar nach. Lernen Sie die Vorteile der Onlineregistrierung Ihrer Kopie von Windows XP kennen.""",
         u"""Durch die Verkn\xFCpfung von Computern in einem Netzwerk wird deren Leistung betr\xE4chtlich erh\xF6ht, und Sie k\xF6nnen sogar Geld sparen Haben Sie mehrere Computer zu Hause? Durch Einrichten eines Netzwerks ergeben sich folgende M\xF6glichkeiten:""",
         u"""Gemeinsame Nutzung einer einzelnen Internetverbindung. Microsoft\xAE Windows\xAE XP enth\xE4lt das Feature Internetverbindungsfreigabe (Internet Connection Sharing, ICS). Durch ICS wird die Internetverbindung eines Computers, der den Host der gemeinsam genutzten Internetverbindung darstellt, f\xFCr alle anderen Computer des Netzwerks freigegeben. Durch die Freigabe einer Internetverbindung k\xF6nnen Sie mit einem Computer im Internet surfen, w\xE4hrend ein anderes Familienmitglied mit einem anderen Computer E-Mails abruft. """,
         u"""Gemeinsame Nutzung von Druckern, Scannern und anderer Hardware. M\xF6glicherweise besitzen Sie einen Drucker, der mit einem Computer in einem anderen Zimmer verbunden ist. In einem Heimnetzwerk k\xF6nnen Sie auf diesem Drucker von Ihrem Computer aus drucken. Es ist nicht mehr erforderlich, Dateien auf Diskette zu speichern und diese in den mit dem Drucker verbundenen Computer einzulegen.""",
         u"""Gemeinsame Verwendung von Dateien und Ordnern. Angenommen, Sie sollen sich einen Schulaufsatz Ihres Kindes ansehen, der auf dem Computer im Kinderzimmer gespeichert ist. Wenn die Computer vernetzt sind, k\xF6nnen Sie z. B. die Datei von Ihrem Computer aus \xF6ffnen, \xE4nderungen vornehmen und die Datei dann auf dem Computer Ihres Kindes speichern.""",
         u"""Au\xDFerdem bestehen weitere Vorteile: Microsoft Windows XP macht das Einrichten eines Heimnetzwerks leichter denn je. Zuerst m\xFCssen Sie jedoch die Computer miteinander verbinden, indem Sie auf jedem die erforderliche Hardware installieren und mit Kabeln oder durch eine drahtlose Technologie verbinden. In diesem Artikel wird das Verfahren von Anfang bis Ende erl\xE4utert. Sie erfahren, wie Sie die f\xFCr Ihre Zwecke geeignete Netzwerktechnologie ausw\xE4hlen, die richtigen Komponenten erwerben und diese ordnungsgem\xE4\xDF installieren und miteinander verbinden.""",
         u"""Au\xDFerdem wird in einem Abschnitt der Schutz des Heimnetzwerks gegen Angriffe von au\xDFen durch Errichtung einer Sicherheitsbarriere erl\xE4utert, einem so genannten Firewall, der auch in Unternehmen eingesetzt wird.""",
        ]]
        doLayout ("Hyphenation for plain text paragraphs", testdata, colWidths, outPDF)


class StyledtextTestCase(unittest.TestCase):
    "Testing hyphenation in a styled text paragraphs (containing markup)."

    def test(self):
        outPDF = "test_styled.pdf"

        # Column widths in mm
        colWidths = [29,44,59,74]

        # Some test data in German.
        testdata = \
        [u"<para>Mit <i>Silbentrennungsverfahren</i> werden extrem lange W\xF6rter, die im deutschen Sprachgebrauch allt\xE4glich sind, automatisch in kleinere Bestandteile zerlegt, wobei die Lesbarkeit nach M\xF6glichkeit erhalten bleiben sollte.</para>",
         u"<para>Die nachfolgenden S\xE4tze sind weitgehend v\xF6llig sinnlos. Sie enthalten aber teilweise besonders sch\xF6n lange zusammengesetzte W\xF6rter, damit der Silbentrennungsalgorithmus auch tats\xE4chlich sichtbar \xFCberpr\xFCft werden kann.</para>",
         u"""<para>Unter <i><a href="http://www.hohenlimburg.de">hohenlimburg.de</a></i> wird in Zusammenarbeit mit Prof. Dr. Gerhard E. Sollbach und Dr. Stephanie Marra M.A., Universit\xE4t Dortmund / Ruhr-Universit\xE4t Bochum, sowie anderen Fachwissenschaftlern ein Online-Portal zur Geschichte der mittelalterlichen Burganlage und fr\xFChneuzeitlichen Ortschaft sowie zu der bis 1807 autonomen Grafschaft Limburg vorbereitet. Grafschaft und Gemeinde Limburg k\xF6nnen auf eine reiche und vielf\xE4ltige Geschichte zur\xFCckblicken, die bis ins Hochmittelalter zur\xFCckreicht.<para>""",
         u"<para>Ein formatierter Absatz mit zwei <b>fetten Worten</b> und einem Wort, das nur einen Teil <i>hervor</i>gehoben hat.</para>",
         u"<para>Der Bundeskanzler arbeitet im <font size='12'>Bundeskanzler</font>amt.</para>",
         u"<para><font size='12' color='blue'>ReportLab</font> erlaubt auch die Verwendung von HTML-Markup im Text zur <b>Hervorhebung</b> einzelner W\xF6rter, <i>ganzer Wortfolgen</i>, oder auch nur von Bestand<font color='green'>t</font><font color='red'></font><font color='brown'>e</font>ilen in <em>zusammen</em>gesetzten W\xF6rtern. </para>",
         u'''<para>Die eingebaute Funktion <font name=Courier>range(i, j [, stride])</font> erzeugt eine Liste von Ganzzahlen und f\374llt sie mit Werten <font name=Courier>k</font>, f\374r die gilt: <font name=Courier>i &lt;= k &lt; j</font>. Man kann auch eine optionale Schrittweite angeben. Die eingebaute Funktion <font name=Courier>xrange()</font> erf\374llt einen \344hnlichen Zweck, gibt aber eine unver\344nderliche Sequenz vom Typ <font name=Courier>XRangeType</font> zur\374ck. Anstatt alle Werte in der Liste abzuspeichern, berechnet diese Liste ihre Werte, wann immer sie angefordert werden. Das ist sehr viel speicherschonender, wenn mit sehr langen Listen von Ganzzahlen gearbeitet wird. <font name=Courier>XRangeType</font> kennt eine einzige Methode, <font name=Courier>s.tolist()</font>, die seine Werte in eine Liste umwandelt.</para>''',
         u"<para>Neu bei <font size='12' color='blue'>ReportLab 2.1</font>:<br />Mit dem br-Tag sind nun auch feste Zeilenumbr\xFCche innerhalb eines Absatzes m\xF6glich. Außerdem kann nun mit strike Zeichen durchgestrichen werden, auch mitten im W<strike>or</strike>t: <b><i>Silben</i>tre<strike>nn</strike>ungsalgorithmus</b> </para>",
        ]
        doLayout ("Hyphenation for styled text paragraphs", testdata, colWidths, outPDF)



class ShyTestCase(unittest.TestCase):
    "Test if the SHY character is rendered correctly."

    def test(self):
        outPDF = "test_shy.pdf"

        # Column widths in mm
        colWidths = [29,44,59,74]

        # Some test data in German.
        testdata = \
        [u"<para>Kapit\xE4ns\xADm\xFCtzen\xADschirm\xADband</para>",
        ]
        doLayout ("A word containing shy characters", testdata, colWidths, outPDF)


class AutoColumnWidthTestCase(unittest.TestCase):
    "Testing hyphenation within a table with no column widths specified."

    def test(self):
        outPDF = "test_autocolwidths.pdf"

        # Column widths in mm
        colWidths = None

        # Some test data in German.
        testdata = \
        [u"<para>Mit <i>Silbentrennungsverfahren</i> werden extrem lange W\xF6rter, die im deutschen Sprachgebrauch allt\xE4glich sind, automatisch in kleinere Bestandteile zerlegt, wobei die Lesbarkeit nach M\xF6glichkeit erhalten bleiben sollte.</para>",
         u"<para>Dieser Absatz hat nur sehr kurze Wörter.</para>",
         u"<para>Der hier erst recht!</para>",
         u"<para>Der Bundeskanzler arbeitet im <font size='12'>Bundeskanzler</font>amt.</para>",
        ]
        
        pagesize = pagesizes.portrait(pagesizes.A4)

        tablestyle = TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                                 ('BOX', (0,0), (-1,-1), 1, colors.black),
                                 ('BACKGROUND', (0,0), (-1,0), colors.orange),
                                 ('INNERGRID', (0,1), (-1,-1), 0.5, colors.black),
                                 ('LEFTPADDING', (0,0), (-1,-1), 3),
                                 ('RIGHTPADDING', (0,0), (-1,-1), 3),
                                ])

        doc = SimpleDocTemplate(outPDF, title="Hyphenation for styled text paragraphs",
                                pagesize=pagesize, allowSplitting=1)
        story = []
    
        header = ["Col%d" % (i+1) for i in range(4)]
        tabContent = [header]
        row = [makeParagraphs(txt,cellStyle) for txt in testdata]
        tabContent.append(row)
        row = [makeParagraphs((u"Zeile 2 Spalte %i" % (i+1)),cellStyle) for i in range(4)]
        tabContent.append(row)
        table = LongTable(tabContent, colWidths=colWidths, style=tablestyle, repeatRows=1)
        story.append(table)
        doc.build(story,onFirstPage=myFirstPage,onLaterPages=myLaterPages)


if __name__ == "__main__":
    unittest.main()