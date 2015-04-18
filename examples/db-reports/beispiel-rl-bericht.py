#!/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright Triestram & Partner GmbH 2010
# 
# Henning von Bargen, Mai 2010

import sys
from easy_reports import *
        
# report-specific classes

class DEPT(DBRecord):

    meta = [("deptno", "Abteilung"),
             ("dname", "Name"),
             ("loc", "Ort"),
           ]
           
class EMP(DBRecord):

    meta = [("empno", "MA-Nr."),
            ("ename", "Name"),
            ("sal", "Gehalt"),
            ("comm", "Prämie"),
            ("hiredate", "Einstellungsdatum"),
           ]

class MyDataModel(DataModel):
        
    def generate(self, with_emp=True):
        data = []
        conn = self.datasource.conn
        cur_dept = conn.cursor()
        cur_emp = conn.cursor()
        cur_dept.execute(
        """
        select deptno, dname, loc 
        from DEPT
        order by deptno
        """)
        for rec in cur_dept:
            dept = DEPT(rec)
            data.append(dept)
            if with_emp:
                cur_emp.execute(
                """
                select empno, ename, sal, comm, hiredate
                from EMP
                where EMP.deptno = :pi_deptno
                order by 1, 2
                """, pi_deptno = dept.deptno)
                emp_list = []
                for rec in cur_emp:
                    emp = EMP(rec)
                    emp_list.append(emp)
                dept.children = {"emp": emp_list}
        self.data = data
        #print self.data
        return self.data

from reportlab.lib.units import inch,cm,mm
from reportlab.lib import pagesizes
from reportlab.lib import enums
from reportlab.platypus.doctemplate import SimpleDocTemplate
from wordaxe.rl.styles import getSampleStyleSheet
from wordaxe.rl.paragraph import Paragraph
from reportlab.platypus.tables import LongTable
from reportlab.platypus import TableStyle
from reportlab.lib import colors

import wordaxe
from wordaxe.DCWHyphenator import DCWHyphenator
wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE',5)

        
class MyLayout(Layout):

    def generatePDF(self, model_data):
        """
        Dieses Beispiel zeigt nicht annähernd die Möglichkeiten von ReportLab!
        Es demonstriert nur, wie einfach es sein kann.
        """
        stylesheet = getSampleStyleSheet()
        # Formatstil für die Überschrift festlegen
        sth1 = stylesheet['Heading1']
        # Formatstil für den Absatz festlegen
        stn = stylesheet['Normal']
        stn.fontName = 'Helvetica'
        stn.fontSize = 10
        stn.leading = 12
        #print stn.spaceAfter
        #print stn.spaceBefore
        #print stn.leading
        
        print("TODO: Why is the text so close to the top of the cells?")
        
        # Automatische Silbentrennung für diesen Stil einschalten
        stn.language = 'DE'
        stn.hyphenation = True
        
        # Wir machen erstmal einen Fake,
        # nämlich den ASCII-Text zeilenweise.
        self.generateDUMP(model_data)
        pure_text = "".join(self.text)
        story = []
        para = Paragraph("Beispiel für einen Datenbankbericht".decode("iso-8859-1"), sth1)
        '''
        story.append(para)
        
        para = Paragraph("""Dies ist ein längerer Absatz, der eigentlich nur den Zweck hat,
die automatische Silbentrennung von WordAxe zu demonstrieren. Aus diesem Grund enthält dieser
Absatz auch einige besonders schöne lange Wörter wie etwa "Donaudampfschifffahrtsgesellschaftskapitän"
oder "Bundeskanzleramt" oder "Landesgesundheitsbehörden", sogar gleich mehrfach:
Schiff Dampfschiff Dampfschifffahrt Donaudampfschiffahrt oder Donaudampfschiffahrtsgesellschaft
Donaudampfschiffahrtsgesellschaftsvorsitzender (Ha! damit habt Ihr wohl nicht gerechnet, oder?)
und nebenbei auch HTML-Formatierung wie <b>fett</b> oder <i>kursiv!</i>
Mal sehen, ob das Euro-Zeichen geht - ich befürchte aber, dass das auf Anhieb nicht funktioniert.
Hier kommt es: € - nee, das sehe ich schon im Quelltext nicht richtig.
""".decode("iso-8859-1"), stn)        
        story.append(para)
        for line in pure_text.splitlines():
            para = Paragraph(line.decode("iso-8859-1"), stn)
            story.append(para)
        '''
        
        # Jetzt mal anders: 
        # Ausgabe als Master-Detail-Liste, wobei die Details
        # eine Spalte weiter eingerückt sind.
        if model_data:
            headers1 = [Paragraph(toUnicode(x), stn) for x in DEPT.headers()]
            headers2 = [None] + [Paragraph(toUnicode(x), stn) for x in EMP.headers()]
            nColumns = max(len(headers1), len(headers2))
            fill1 = ([None] * (nColumns - len(headers1)))
            fill2 = ([None] * (nColumns - len(headers2)))
            headers1 += fill1
            headers2 += fill2
            tableData = [headers1, headers2]
            colWidths = [None] * nColumns
            colWidths[-1]=40*mm
            nRows = len(model_data)
            tableStyle = TableStyle([('BOX', (0,0), (-1,-1), 1, colors.black),
                                     ('BACKGROUND', (0,0), (-1,1), colors.orange),
                                     ('BACKGROUND', (0,1), (-1,1), colors.yellow),
                                     ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
                                     ('LEFTPADDING', (0,0), (-1,-1), 3),
                                     ('RIGHTPADDING', (0,0), (-1,-1), 3),
                                     ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                     ])
            for dept in model_data:
                tableData.append(dept.genParagraphList(stn) + fill1)
                tableStyle.add('BACKGROUND', (0,len(tableData)-1), (-1,len(tableData)-1), colors.orange)
                for emp in dept.children["emp"]:
                    tableData.append([""] + emp.genParagraphList(stn) + fill2)            table = LongTable(tableData, style=tableStyle, colWidths=colWidths, repeatRows=2)
            story.append(table)
        self.story = story

class MyReport(Report):
    Layout = MyLayout
    DataModel = MyDataModel

if __name__ == "__main__":
    report = MyReport(sys.argv)
    datasource = OracleDataSource("hvb", "x", "//127.0.0.1:1521/xe")
    destinations = [(Layout.DUMP, "ausgabe.txt"),
                    (Layout.PDF, "ausgabe.pdf"),
                    (Layout.XML, "ausgabe.xml"),
                   ]
    report.setup(datasource, destinations)
    report.run()
    