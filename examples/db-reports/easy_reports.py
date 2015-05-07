#!/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright Triestram & Partner GmbH 2010
# 
# Henning von Bargen, Mai 2010

# Unicode type compatibility for Python 2 and 3
import sys
if sys.version < '3':
    unicode_type = unicode
else:
    unicode_type = str

# Imports for OracleDataSource
import cx_Oracle 

class OracleDataSource(object):

    def __init__(self, username, password, dsn):
        self.username = username
        self.password = password
        self.dsn = dsn

    def connect(self):
        print("Connecting as %s@%s" % (self.username, self.dsn))
        connstr = "%s/%s@%s" % (self.username, self.password, self.dsn)
        self.conn = cx_Oracle.connect(connstr)
        
    def close(self):
        self.conn.close()
        del self.conn
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()

from xml.etree.ElementTree import Element, SubElement, ElementTree
from xml.sax import saxutils

def toUnicode(val):
        if type(val) == list:
            return [toUnicode(x) for x in val]
        if type(val) == tuple:
            return tuple(*[toUnicode(x) for x in val])
        if type(val) == dict:
            d = dict()
            for k,v in val.items():
                d[k] = toUnicode(v)
            return d
        if type(val) == unicode_type:
            return val
        if type(val) == str:
            return val.decode("iso-8859-1") # only for Python 2
        return unicode_type(val)
        
class DBRecord(object):
    
    def from_record(self, record, metaDef=None):
        if metaDef is None:
            metaDef = self.meta
        if len(metaDef) != len(record):
            raise Exception("Anzahl Spalten passt nicht zu Metadaten!")
        if metaDef is None:
            metaDef = [("Column%d" % (i+1)) for i in range(len(record))]
        for info, value in zip(metaDef, record):
            if type(info) is tuple:
                name = info[0]
            else:
                name = info
            setattr(self, name, value)

    @classmethod
    def columns(cls):
        retlist = []
        for coldef in cls.meta:
            if type(coldef) is tuple:
                column, title = coldef
            else:
                column, title = coldef, coldef.title()
            retlist.append(column)
        return retlist

    @classmethod
    def headers(cls):
        retlist = []
        for coldef in cls.meta:
            if type(coldef) is tuple:
                column, title = coldef
            else:
                column, title = coldef, coldef.title()
            retlist.append(title)
        return retlist
        
    def values(self):
        return [getattr(self,x) for x in self.columns()]        

    def genParagraphList(self, style):
        return [Paragraph(toUnicode(value), style) for value in self.values()]
        
    def dump(self, indent=0, recursion_level=99):
        buf = []
        buf.append(" " * indent)
        meta = self.meta
        buf.append("%s (" % self.__class__.__name__)
        for coldef in meta:
            if coldef is not meta[0]:
                buf.append(", ")
            if type(coldef) is tuple:
                column, title = coldef
            else:
                column, title = coldef, coldef.title()
            buf.append(title + ": ")
            buf.append("%s" % getattr(self, column))
        if recursion_level > 0:
            children = getattr(self, "children", {})
            if children:
                buf.append("\n")
            for child_name in sorted(children.keys()):
                buf.append(" " * (indent + 4) + "---- %s : %d\n" % (child_name, len(children[child_name])))
                for child in children[child_name]:
                    buf.append(child.dump(indent + 4, recursion_level - 1))
        buf.append(")\n")
        return "".join(buf)

    def __str__(self):
        return self.dump(indent=0, recursion_level=99)
        
    def __repr__(self):
        buf = []
        meta = self.meta
        buf.append("%s(" % self.__class__.__name__)
        for coldef in meta:
            if coldef is not meta[0]:
                buf.append(", ")
            if type(coldef) is tuple:
                column, title = coldef
            else:
                column, title = coldef, coldef.title()
            buf.append(column + "=")
            buf.append("%r" % getattr(self, column))
        children = getattr(self, "children", {})
        for child_name in sorted(children.keys()):
            buf.append(", %s=[" % child_name)
            for child in children[child_name]:
                if child is not children[child_name][0]:
                    buf.append(", ")
                buf.append(repr(child))
            buf.append(")")
        buf.append(")")
        return "".join(buf)
        
    def toXML(self, parent, recursion_level = 99):
        elem = SubElement(parent, self.__class__.__name__) 
        meta = self.meta
        for coldef in meta:
            if type(coldef) is tuple:
                column, title = coldef
            else:
                column, title = coldef, coldef.title()
            subelem = SubElement(elem, column)
            value = getattr(self, column)
            if value is not None:
                if not isinstance(value, (str, unicode_type)):
                    value = str(value)
                subelem.text = saxutils.escape(value)
        if recursion_level > 0:
            children = getattr(self, "children", {})
            for child_name in sorted(children.keys()):
                for child in children[child_name]:
                    child.toXML(elem, recursion_level - 1)
        return elem
        
    def __init__(self, record):
        self.from_record(record)


class DataModel(object):

    def __init__(self, datasource):
        self.datasource = datasource
        self.datasource.connect()
        
    def generate(self, with_rejp=True):
        data = []
        conn = self.datasource.conn
        self.data = []

        
# Imports for Layout
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate
from wordaxe.rl.paragraph import Paragraph
import reportlab.lib.styles

class Layout(object):

    DUMP = "DUMP"
    PDF = "PDF"
    XML = "XML"

    def __init__(self, report, format, fname):
        self.report = report
        self.format = format
        self.fname = fname
        
    def generate(self, model_data):
        func = getattr(self, "generate" + self.format)
        return func(model_data)
        
    def save(self):
        func = getattr(self, "save" + self.format)
        return func()
    
    def generateDUMP(self, model_data):
        # dummy
        self.text = []
        self.text.append("Ausgabe:\n")
        for rec in model_data:
            self.text.append(rec.dump())

    def saveDUMP(self):
        fh = open(self.fname, "wt", 32768)
        for frag in self.text:
            fh.write(frag)
        fh.close()
        
    def generatePDF(self, model_data):
        """
        Dieses Beispiel zeigt nicht annähernd die Möglichkeiten von ReportLab!
        Es demonstriert nur, wie einfach es sein kann.
        """
        stylesheet = getSampleStyleSheet()
        stn = stylesheet['Normal']
        text = """
PDF Layout not implemented.<br>
Please add a method <font face="Courier">generatePDF(self, data_model)</font>
to your Layout class.
The method should generate a ReportLab Platypus story from the data_model
and store it in <font face="Courier">self.story</font>.
"""
        para = Paragraph(text.decode("iso-8859-1"), stn)
        self.story = [para]

    def savePDF(self):
        # Hier findet eigentlich erst die Formatierung
        # vollautomatisch durch ReportLab statt...
        doc = SimpleDocTemplate(self.fname)
        doc.build(self.story)
        
    def generateXML(self, model_data):
        self.root = Element("root")
        for d in model_data:
            d.toXML(self.root)

    def saveXML(self):
        tree = ElementTree(self.root)
        tree.write(self.fname, "utf-8")
     

class Report(object):
    
    def __init__(self,args):
        self.args = args
        
    def setup(self, datasource, destinations):
        self.datasource = datasource
        self.destinations = destinations
        
    def run(self):
        datamodel = self.__class__.DataModel(self.datasource)
        print("generating data model...")
        self.data = datamodel.generate()
        for (format, fname) in self.destinations:
            print("generating %s output..." % format)
            layout = self.__class__.Layout(self, format, fname)
            layout.generate(self.data)
            layout.save()
        print("done.")