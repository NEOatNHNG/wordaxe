#!/bin/env/python
# -*- coding: utf-8 -*-

# Helper classes for the new Paragraph-Implementation

import reportlab.pdfbase.pdfmetrics as pdfmetrics
from reportlab.lib.abag import ABag

from wordaxe.hyphen import HyphenationPoint, SHY, HyphenatedWord

class Style(ABag):
    "This is used to store style attributes."

class Fragment(object):
    "A fragment representing a piece of text or other information"
    
class StyledFragment(Fragment):
    def __init__(self, style):
        self.style = style

    @staticmethod
    def str_width(text, style):
        "Compute the width of a styled text"
        return pdfmetrics.stringWidth(text, style.fontName, style.fontSize)

    def __repr__(self):
        return self.__class__.__name__
    __str__ = __repr__
        
class StyledText(StyledFragment):    
    "A string in some style"
    def __init__(self, text, style):
        assert isinstance(text, unicode)
        super(StyledText, self).__init__(style)
        self.text = text
        self.width = self.str_width(text, style)
        self.ascent, self.descent = pdfmetrics.getAscentDescent(style.fontName, style.fontSize)

    def __str__(self):
        return "ST(%s)" % self.text.encode("utf-8")
        
    __repr__ = __str__

    @staticmethod
    def fromParaFrag(frag):
        "This allows to reuse the good old paraparser.py"
        text = frag.text
        if not isinstance(text, unicode):
            text = unicode(text, "utf-8")
        return StyledText(text, frag)
        
class StyledWhiteSpace(StyledFragment):
    "Used for every token that delimits words."

class StyledSpace(StyledWhiteSpace):
    "A spacer in some style"
    def __init__(self, style, text=u" "):
        super(StyledSpace, self).__init__(style)
        self.text = unicode(text)
        self.width = self.str_width(text, style)

    def __str__(self):
        return "SP(%s)" % self.text.encode("utf-8")

    __repr__ = __str__
        
class StyledNewLine(StyledWhiteSpace):
    "A new line"

    def __str__(self):
        return "NL"

    __repr__ = __str__

class StyledWord(Fragment):
    "A word compound of some styled strings"

    def __init__(self, fragments):
        for frag in fragments: assert isinstance(frag, StyledText)
        self.fragments = fragments
        # Breite berechnen
        self.text = u"".join([f.text for f in fragments])
        self.width = sum([f.width for f in fragments])
        
    def __str__(self):
        return "SW(%s)" % self.text.encode("utf-8")
        
    __repr__ = __str__
    
    def splitAt(self, hp):
        """
        Splits the styled word at a given hyphenation point
        (see wordaxe.hyphen).
        The result is a tuple (left, right) of StyledWords.
        Works just like HyphenatedWord.split, but for a StyledWord.
        """
        
        #TODO does not work as expected
        
        text = self.text
        assert isinstance(text, HyphenatedWord)
        # first get the unstyled versions
        left, right = text.split(hp)
        # now restore the styled fragments for left + right
        remaining = self.fragments[:]
        lfrags = list()
        ltext = u""
        rfrags = list()
        rtext = u""
        while remaining and ltext.startswith(ltext + remaining[0].text):
            frag = remaining.pop(0)
            ltext += frag.text
            lfrags.append(frag)
        while remaining and rtext.endswith(remaining[-1].text + rtext):
            frag = remaining.pop(-1)
            rtext = frag.text + rtext
            rfrags.insert(0, frag)
        # Now at most 2 frags might remain.
        # Decide whether they belong to left or right
        assert len(remaining) <= 2
        if remaining:
            if type(hp) is int:
                indx = hp
            else:
                indx = hp.indx
            lfrags.append(StyledText(left[len(ltext):], remaining[0].style))
            if rtext:
                rfrags.insert(0, StyledText(right[:-len(rtext)], remaining[-1].style))
            else:
                rfrags.insert(0, StyledText(right, remaining[-1].style))
        left = StyledWord(lfrags)
        right = StyledWord(rfrags)
        return (left,right)


class Line(object):
    "A single line in the paragraph"
     
    def __init__(self, fragments, width, height, baseline, space_wasted, keepWhiteSpace):
        for frag in fragments: assert isinstance(frag, Fragment)
        self.fragments = fragments
        self.width = width
        #print fragments
        #print "Line width:", width, sum(getattr(f, "width",0) for f in fragments)
        assert abs(self.width - sum(getattr(f,"width",0) for f in fragments)) <= 1e-5
        self.height = height
        self.baseline = baseline
        assert 0 <= self.baseline
        assert baseline <= height
        self.space_wasted = space_wasted
        # kill WhiteSpace at beginning and end of line
        if not keepWhiteSpace:
            while self.fragments and isinstance (self.fragments[0], StyledWhiteSpace):
                ws = self.fragments.pop(0)
                self.width -= ws.width
                self.space_wasted += ws.width
            while self.fragments and isinstance (self.fragments[-1], StyledWhiteSpace):
                ws = self.fragments.pop(-1)
                self.width -= ws.width
                self.space_wasted += ws.width
            # TODO: What to do with two differently styled spaces 
            #       in the middle of the line?

        # Compute font size
        max_size = 0
        max_ascent = min_descent = 0
        for frag in self.iter_flattened_frags():
            if isinstance(frag, StyledText):
                size = getattr(frag.style, "fontSize", 0)
                ascent, descent = frag.ascent, frag.descent
                if not max_size:
                    max_size = size
                    max_ascent = ascent
                    max_descent = descent
                else:
                    max_size = max(max_size, size)
                    max_ascent = max(max_ascent, ascent)
                    min_descent = min(min_descent, descent)
        self.fontSize = max_size
        self.ascent = max_ascent
        self.descent = min_descent
         
    def __str__(self):
        return "Line(%s)" % (",".join(str(frag) for frag in self.fragments))
     
    __repr__ = __str__
    

    def iter_flattened_frags(self):
        """
        Returns the fragments flattened (one word may contribute several fragments).
        """
        for frag in self.fragments:
            if isinstance(frag, StyledWord):
                for f in frag.fragments:
                    yield f
            else:
                yield frag
