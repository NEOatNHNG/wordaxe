#!/bin/env python
# -*- coding: iso-8859-1 -*-
#Copyright ReportLab Europe Ltd. 2000-2004
#
#see license.txt for license details
#history http://www.reportlab.co.uk/cgi-bin/viewcvs.cgi/public/reportlab/trunk/platypus/paragraph.py
#$Header: /cvsroot/deco-cow/hyphenation/reportlab/platypus/paragraph.py,v 1.1.1.1 2004/04/27 21:19:02 hvbargen Exp $
#
# @CHANGED Henning von Bargen, added hyphenation support.

# Stand: Wie reportlab.platypus.paragraph.py vom 04.Oktober 2007 (1. Version)

__version__=''' paragraph.py, V 1.0,  Henning von Bargen, $Revision:  1.0 '''

from types import StringType, ListType, UnicodeType, TupleType

from reportlab.platypus.paragraph import *
del ParaParser
from wordaxe.rl.paraparser import ParaParser
_parser=ParaParser()
from reportlab.platypus.paragraph import _getFragWords, _sameFrag, _putFragLine
from reportlab.platypus.paragraph import _justifyDrawParaLineX, _doLink
from reportlab.platypus.paragraph import _split_blParaSimple, _split_blParaHard
from reportlab.platypus.paragraph import _drawBullet, _handleBulletWidth
from reportlab.platypus.paragraph import _56, _16
import traceback
import copy
from wordaxe import SHY, hyphRegistry, hyphen, HyphenatedWord, HyphenationPoint

def myjoin(tlist, joiner=u" "):
    return joiner.join((isinstance(t,unicode) and t or t.decode("utf8")) for t in tlist)


class HVBDBG:
    @staticmethod
    def s(obj):
        if type(obj) == list:
            return "[" + ", ".join([HVBDBG.s(x) for x in obj]) + "]"
        elif type(obj) == tuple:
            return "(" + ", ".join([HVBDBG.s(x) for x in obj]) + ")"
        elif isinstance(obj, ParaLines):
            if hasattr(obj, "lines"):
                return "ParaLines(.lines=" + HVBDBG.s(obj.lines) + ")"
            else:
                return "ParaLines(%s)" % dir(obj)
        elif isinstance(obj, FragLine):
            return "FragLine(.words=" + HVBDBG.s(obj.words) + ")"
        elif isinstance(obj, ABag):
            return "ABag(.text=%r)" % obj.text
        elif type(obj) == float:
            return "%1.2f" % obj
        else:
            return repr(obj)

# Anpassungen hier jeweils: myjoin statt join, if extraspace<0: _justify...
def _leftDrawParaLine( tx, offset, extraspace, words, last=0):
    if extraspace<0:
        return _justifyDrawParaLine(tx,offset,extraspace,words,last)
    setXPos(tx,offset)
    tx._textOut(myjoin(words),1)
    setXPos(tx,-offset)
    return offset

def _centerDrawParaLine( tx, offset, extraspace, words, last=0):
    if extraspace<0:
        return _justifyDrawParaLine(tx,offset,extraspace,words,last)
    m = offset + 0.5 * extraspace
    setXPos(tx,m)
    tx._textOut(myjoin(words),1)
    setXPos(tx,-m)
    return m

def _rightDrawParaLine( tx, offset, extraspace, words, last=0):
    if extraspace<0:
        return _justifyDrawParaLine(tx,offset,extraspace,words,last)
    m = offset + extraspace
    setXPos(tx,m)
    tx._textOut(myjoin(words),1)
    setXPos(tx,-m)
    return m

from reportlab.platypus.paragraph import _leftDrawParaLineX as _orig_leftDrawParaLineX
def _leftDrawParaLineX( tx, offset, line, last=0):
    if line.extraSpace<0:
        return _justifyDrawParaLineX(tx,offset,line,last)
    return _orig_leftDrawParaLineX( tx, offset, line, last)

from reportlab.platypus.paragraph import _centerDrawParaLineX as _orig_centerDrawParaLineX
def _centerDrawParaLineX( tx, offset, line, last=0):
    if line.extraSpace<0:
        return _justifyDrawParaLineX(tx,offset,line,last)
    return _orig_centerDrawParaLineX( tx, offset, line, last)

from reportlab.platypus.paragraph import _rightDrawParaLineX as _orig_rightDrawParaLineX
def _rightDrawParaLineX( tx, offset, line, last=0):
    if line.extraSpace<0:
        return _justifyDrawParaLineX(tx,offset,line,last)
    return _orig_rightDrawParaLineX( tx, offset, line, last)

# this routine is copied from the original (just because we are using "join" here).
def _justifyDrawParaLine( tx, offset, extraspace, words, last=0):
    setXPos(tx,offset)
    text = myjoin(words)
    if last:
        #last one, left align
        tx._textOut(text,1)
    else:
        nSpaces = len(words)-1
        if nSpaces:
            tx.setWordSpace(extraspace / float(nSpaces))
            tx._textOut(text,1)
            tx.setWordSpace(0)
        else:
            tx._textOut(text,1)
    setXPos(tx,-offset)
    return offset

# this routine is copied from the original (just because we are using "join" here).
def _do_under_line(i, t_off, ws, tx, lm=-0.125):
    y = tx.XtraState.cur_y - i*tx.XtraState.style.leading + lm*tx.XtraState.f.fontSize
    textlen = tx._canvas.stringWidth(myjoin(tx.XtraState.lines[i][1]), tx._fontname, tx._fontsize)
    tx._canvas.line(t_off, y, t_off+textlen+ws, y)

# this routine is copied from the original (just because we are using "join" here).
def _do_link_line(i, t_off, ws, tx):
    xs = tx.XtraState
    leading = xs.style.leading
    y = xs.cur_y - i*leading - xs.f.fontSize/8.0 # 8.0 factor copied from para.py
    text = myjoin(xs.lines[i][1])
    textlen = tx._canvas.stringWidth(text, tx._fontname, tx._fontsize)
    _doLink(tx, xs.link, (t_off, y, t_off+textlen+ws, y+leading))

# this routine is copied from the original (just because we are using "join" here).
from reportlab.platypus.paragraph import _do_post_text

from reportlab.platypus.paraparser import ParaFrag

def _getFragWords(frags):
    ''' given a Parafrag list return a list of fragwords
        [[size, (f00,w00), ..., (f0n,w0n)],....,[size, (fm0,wm0), ..., (f0n,wmn)]]
        each pair f,w represents a style and some string
        each sublist represents a word
    '''
    R = []
    W = []
    n = 0
    hangingStrip = False
    for f in frags:
        text = f.text
        #del f.text # we can't do this until we sort out splitting
                    # of paragraphs
        if text!='':
            if hangingStrip:
                hangingStrip = False
                text = text.lstrip()
            S = split(text)
            if S==[]: S = ['']
            if W!=[] and text[0] in whitespace:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0

            for w in S[:-1]:
                W.append((f,w))
                n += stringWidth(w, f.fontName, f.fontSize)
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0

            w = S[-1]
            W.append((f,w))
            n += stringWidth(w, f.fontName, f.fontSize)
            if text and (text[-1] in whitespace or text.endswith(hyphen.SHY.encode('utf8'))):
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0
        elif hasattr(f,'cbDefn'):
            w = getattr(f.cbDefn,'width',0)
            if w:
                if W!=[]:
                    W.insert(0,n)
                    R.append(W)
                    W = []
                    n = 0
                R.append([w,(f,'')])
            else:
                W.append((f,''))
        elif hasattr(f, 'lineBreak'):
            #pass the frag through.  The line breaker will scan for it.
            if W!=[]:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0
            R.append([0,(f,'')])
            hangingStrip = True

    if W!=[]:
        W.insert(0,n)
        R.append(W)

    return R


def _split_blParaHard(blPara,start,stop):
    f = []
    lines = blPara.lines[start:stop]
    for l in lines:
        for w in l.words:
            f.append(w)
        if l is not lines[-1]:
            i = len(f)-1
            while i>=0 and hasattr(f[i],'cbDefn') and not getattr(f[i].cbDefn,'width',0): i -= 1
            if i>=0:
                g = f[i]
                if not g.text: g.text = ' '
                elif g.text.endswith(hyphen.SHY.encode('utf8')): pass # = hyphen.shy
                elif g.text[-1]!=' ': g.text += ' '
    return f


# Here, we are changing the breakLines-Routine etc.
_orig_Paragraph = Paragraph
class Paragraph(_orig_Paragraph):
    """
    This class is a modification of the reportlab.platypus.paragraph.Paragraph
    class, adding support for automatic hyphenation.
    For this to work, just define two additional for the paragraph style:
    hyphenation (boolean): Set this to True to enable hyphenation.
    language: a language string. It is used as a key for the 
    wordaxe.hyphRegistry, which returns a Hyphenator instance.
    It is recommended to use ISO 639 2 or 3 character codes for the language.
    """

    def _setup(self, text, style, bulletText, frags, cleaner):
        if frags is None:
            _parser.setEncoding(self.encoding)
        return _orig_Paragraph._setup(self, text, style, bulletText, frags, cleaner)

    def split(self,availWidth, availHeight):
        if len(self.frags)<=0: return []

        #the split information is all inside self.blPara
        if not hasattr(self,'blPara'):
            self.wrap(availWidth,availHeight)
        blPara = self.blPara
        style = self.style
        autoLeading = getattr(self,'autoLeading',getattr(style,'autoLeading',''))
        leading = style.leading
        lines = blPara.lines
        if blPara.kind==1 and autoLeading not in ('','off'):
            s = height = 0
            if autoLeading=='max':
                for i,l in enumerate(blPara.lines):
                    h = max(1.2*l.fontSize,leading)
                    n = height+h
                    if n>availHeight+1e-8:
                        break
                    height = n
                    s = i+1
            elif autoLeading=='min':
                for i,l in enumerate(blPara.lines):
                    h = 1.2*l.fontSize
                    n = height+1.2*l.fontSize
                    if n>availHeight+1e-8:
                        break
                    height = n
                    s = i+1
            else:
                raise ValueError('invalid autoLeading value %r' % autoLeading)
        else:
            l = leading
            if autoLeading=='max':
                l = max(leading,1.2*style.fontSize)
            elif autoLeading=='min':
                l = 1.2*style.fontSize
            s = int(availHeight/l)
            height = s*l

        n = len(lines)
        allowWidows = getattr(self,'allowWidows',getattr(self,'allowWidows',1))
        allowOrphans = getattr(self,'allowOrphans',getattr(self,'allowOrphans',0))
        if not allowOrphans:
            if s<=1:    #orphan?
                del self.blPara
                return []
        if n<=s: return [self]
        if not allowWidows:
            if n==s+1: #widow?
                if (allowOrphans and n==3) or n>3:
                    s -= 1  #give the widow some company
                else:
                    del self.blPara #no room for adjustment; force the whole para onwards
                    return []
        func = self._get_split_blParaFunc()
        P1=self.__class__(None,style,bulletText=self.bulletText,frags=func(blPara,0,s))
        #this is a major hack
        P1.blPara = ParaLines(kind=1,lines=blPara.lines[0:s],aH=availHeight,aW=availWidth)
        P1._JustifyLast = 1
        P1._splitpara = 1
        P1.height = height
        P1.width = availWidth
        if style.firstLineIndent != 0:
            style = deepcopy(style)
            style.firstLineIndent = 0
        P2=self.__class__(None,style,bulletText=None,frags=copy.deepcopy(func(blPara,s,n)))
        return [P1,P2]

    class OVERFLOW:
         pass
    class SQUEEZE:
         pass
    class HYPHENATE:
         pass

    def rateHyph(self,basePenalty,cline,spaceLeft,spaceWidth):
        """Rate a possible hyphenation point"""
        #### EVTL ist Bewertung falsch, vor allem falls spaceLeft ZU klein ist!
        #print "rateHyph %s %d" % (cline,spaceLeft)
        nSpaces = len(cline)
        if nSpaces:
            stretch = spaceLeft/(nSpaces*spaceWidth)
            if stretch<0:
                stretchPenalty = stretch*stretch*stretch*stretch*5000
            else:
                stretchPenalty = stretch*stretch*30
        else: # HVB 20060907: Kein einziges Wort?
            if spaceLeft>0:
                 stretchPenalty = spaceLeft/spaceWidth*20
            else:
                 stretchPenalty = 20000
        rating = 16384 - basePenalty - stretchPenalty
        return rating
        
    def findBestSolution(self,cLine,word,currentWidth,maxWidth,spaceWidth,fontName,fontSize,trySqueeze):
        """Finds the best solution for the word:
           Should the word OVERFLOW completely to the next line,
           should the renderer SQUEEZE it into the current line,
           or should we HYPHENATE the word and put the left part
           into the current line and let the rest overflow.?
           The return value is a tuple 
           
           (action, left, right, spaceWasted)
           
           where action is one of SQUEEZE, OVERFLOW, HYPHENATE,
           left is the left part of the word that should still go into
           the current line (a string),
           right is the right part of the word that should overflow to
           the next line (a HyphenatedWord),
           and spaceWasted is the space that's wasted in the current line -
           a negative value means that the renderer has to squeeze
           (make spaces narrower than normally).
        """
        if self.style.hyphenation:
            hyphenator = hyphRegistry.get(self.style.language,None)
        else: # Keine Silbentrennung aktiv
            hyphenator = None
        if isinstance(word,HyphenatedWord):
            pass
        else: # HVB20060907 Muss erst HyphenatedWord zum String bestimmen - funktioniert evtl. nicht mit UTF8!
            if isinstance(word, unicode):
                uniword = word
            else:
                uniword = word.decode(self.encoding)
            if hyphenator:
                word = hyphenator.hyphenate(uniword)
                # HVB, 29.04.2008
                if word is None:
                    word = HyphenatedWord(uniword, hyphenations=[])
                #if self.debug and not word.hyphenations and word.info[0] != "NOT_HYPHENATABLE":
                #    print "---- %s : %s" % (word.word,word.info)
            else:
                ### word = HyphenatedWord(word)
                word = HyphenatedWord(uniword, hyphenations=[])
            
        #print "findBestSolution %s %s" % (cLine,word.word)
        if hyphenator is None:
            if len(cLine):
                #FALSCH return (self.OVERFLOW, word, 0, "", maxWidth-currentWidth)
                return (self.OVERFLOW, "", word, maxWidth-currentWidth)
            else:
                wordWidth = stringWidth(word,fontName,fontSize)
                leftWidth = currentWidth + spaceWidth + wordWidth
                return (self.SQUEEZE, word, None, maxWidth-leftWidth)
        # try OVERFLOW
        quality = self.rateHyph(0,cLine,maxWidth-currentWidth,spaceWidth)
        bestSolution = (self.OVERFLOW, "", word, maxWidth-currentWidth)
        #print "OV"
        # try SQUEEZE
        if trySqueeze and len(cLine):
            wordWidth = stringWidth(word,fontName,fontSize)
            leftWidth = currentWidth + spaceWidth + wordWidth
            q = self.rateHyph(0,cLine,maxWidth-leftWidth,spaceWidth)
            if q>quality:
                #print "SQZ"
                bestSolution = (self.SQUEEZE, word, None, maxWidth-leftWidth)
                quality = q
        # try HYPHENATE
        for hp in word.hyphenations:
            left,right = word.split(hp)
            leftWidth = currentWidth + spaceWidth + stringWidth(left, fontName, fontSize, self.encoding)
            q = self.rateHyph(100-10*hp.quality,cLine,maxWidth-leftWidth,spaceWidth)
            #print q,quality
            if q>quality:
                #print "HYPH", left, right.word
                bestSolution = (self.HYPHENATE, left, right, maxWidth-leftWidth)
                quality = q
        if bestSolution[0] is self.OVERFLOW and not cLine:
            # We have to make a hard break in the word
            #print "FORCE Hyphenation"
            # force at least a single character into this line
            left, right = word.split(HyphenationPoint(1,1,0,"",0,""))
            bestSolution = (self.HYPHENATE, left, right, 0)
            for p in range(1,len(word)):
                left,right = word.split(HyphenationPoint(p,1,0,"",0,""))
                if left[-1:] not in ["-",SHY]: 
                    left = left + SHY
                leftWidth = currentWidth + spaceWidth + stringWidth(left, fontName, fontSize, self.encoding)
                if leftWidth <= maxWidth:
                    bestSolution = (self.HYPHENATE, left, right, maxWidth-leftWidth)
                else:
                    # does not fit anymore
                    break
        return bestSolution

# finding bestSolution where the word uses possibly several different font styles
# (action,left,right,spaceWasted) = self.findBestSolutionX(words,w,currentWidth,maxWidth,spaceWidth,windx<len(words))
    def findBestSolutionX(self,words,word,currentWidth,maxWidth,spaceWidth,trySqueeze):

        # Helper functions
        def wWidth(w):
            "Returns the stringwidth of a formatted word."
            width = 0
            p = 0
            for f,s in w[1:]:
                width += stringWidth(s,f.fontName,f.fontSize)
            return width

        def splitWordAt(w,hp):
            """Splits word w into left, right at splitpos.
            ## HVB, 14.10.2006 comment:
            w is a list with at least 3 elements,
            w[0] = a width ?
            w[1] = a tuple (Parafrag, utf8-encoded word to split)
            ...
            w[-1] = the Hyphenatedword object corresponding to the word
            hp is a hyphenation point that determines where and how to split.
            """
            hyphWord = w[-1]
            #print "splitWordAt", repr(hyphWord), hp
            left = [0]
            right = [0]
            width = 0
            n = 0
            stillLeftPart = True
            
            for f,s in w[1:-1]:
              us = s.decode("utf8")
              #print "f=%r, s=%r, us=%r" % (f.text,s,us)
              if stillLeftPart:
                n1 = min(hp.indx-n,len(us))
                s1 = us[:n1]
                #print "n1=%r,s1=%r" % (n1,s1)
                n += n1
                #left.append(f.clone(),
                left.append((f,s1.encode("utf8")))
                if n1 < len(s):
                    right.append((f,us[n1:].encode("utf8")))
                if n>=hp.indx:
                    stillLeftPart = False
              else:
                right.append((f,s))
            #left[-1] = (left[-1][0], left[-1][1][:hp.indx-hp.nl]+hp.sl.encode("utf8"))
            left[-1] = (left[-1][0], left[-1][1]+hp.sl.encode("utf8"))
            right[1] = (right[1][0], hp.sr.encode("utf8")+right[1][1][hp.nr:])
            #print "left[-1][1] = %r" % left[-1][1]
            
            # calculate new widths
            left[0] = wWidth(left)
            right[0] = wWidth(right)
            if hp.nl==0 and hp.sl=="": assert (abs(left[0]+right[0] - w[0]) < 0.001)
            
            # append new hyphenated word to the right part
            right.append(hyphWord.split(hp)[1])
            #print "splitWordAt returns %r, %r" % (left[-1][1], right[-1])
            return left, right        
            
        if self.style.hyphenation:
            hyphenator = hyphRegistry.get(self.style.language,None)
        else: # Keine Silbentrennung aktiv
            hyphenator = None
        hyphWord = word[-1]
        assert isinstance(hyphWord,HyphenatedWord)
            
        #print "findBestSolutionX %s %s" % (words,hyphWord.word)
        if hyphenator is None:
            if len(words):
                #FALSCH return (self.OVERFLOW, word, 0, "", maxWidth-currentWidth)
                return (self.OVERFLOW, "", word, maxWidth-currentWidth)
            else:
                wordWidth = wWidth(word[:-1])
                leftWidth = currentWidth + spaceWidth + wordWidth
                return (self.SQUEEZE, word, None, maxWidth-leftWidth)
        # try OVERFLOW
        quality = self.rateHyph(0,words,maxWidth-currentWidth,spaceWidth)
        bestSolution = (self.OVERFLOW, "", word, maxWidth-currentWidth)
        #print "OV"
        # try SQUEEZE
        if trySqueeze and len(words):
            wordWidth = wWidth(word[:-1])
            leftWidth = currentWidth + spaceWidth + wordWidth
            q = self.rateHyph(0,words,maxWidth-leftWidth,spaceWidth)
            if q>quality:
                #print "SQZ"
                bestSolution = (self.SQUEEZE, word, None, maxWidth-leftWidth)
                quality = q
        # try HYPHENATE
        for hp in hyphWord.hyphenations:
            left,right = splitWordAt(word,hp)
            #print "left: %r" % left
            leftWidth = currentWidth + spaceWidth + left[0]
            #print "leftWidth=%d" % leftWidth
            q = self.rateHyph(100-10*hp.quality,words,maxWidth-leftWidth,spaceWidth)
            if q>quality:
                bestSolution = (self.HYPHENATE, left, right, maxWidth-leftWidth)
                quality = q
        if bestSolution[0] is self.OVERFLOW and not words:
            # We have to make a hard break in the word
            #print "FORCE Hyphenation"
            # force at least a single character into this line
            left, right = word.split(HyphenationPoint(1,1,0,"",0,""))
            bestSolution = (self.HYPHENATE, left, right, 0)
            for p in range(1,len(hyphWord.word)):
                if hyphWord.word[p-1] not in ["-",SHY]:
                    r= SHY
                else:
                    r = ""
                left,right = splitWordAt(word,HyphenationPoint(p,1,0,r,0,""))
                leftWidth = currentWidth + spaceWidth + left[0]
                if leftWidth <= maxWidth:
                    bestSolution = (self.HYPHENATE, left, right, maxWidth-leftWidth)
                else:
                    # does not fit anymore
                    break
        if bestSolution[0] is self.OVERFLOW:
            wordWidth = wWidth(word[:-1])
            #print "bestSolution is OVERFLOW",
            #print "wordWidth=", wordWidth,
            #print "too wide=", currentWidth + spaceWidth + wordWidth - maxWidth

        print "bestSolution:", HVBDBG.s(bestSolution)
        return bestSolution

    # HVB, 20071104 copied from rl paragraph.py.
    # because we need a modified version of _split_blParaHard.
    def _get_split_blParaFunc(self):
        return self.blPara.kind==0 and _split_blParaSimple or _split_blParaHard
    
    def breakLines(self, width):
        """
        Returns a broken line structure. There are two cases

        A) For the simple case of a single formatting input fragment the output is
            A fragment specifier with
                kind = 0
                fontName, fontSize, leading, textColor
                lines=  A list of lines
                        Each line has two items.
                        1) unused width in points
                        2) word list

        B) When there is more than one input formatting fragment the output is
            A fragment specifier with
                kind = 1
                lines=  A list of fragments each having fields
                            extraspace (needed for justified)
                            fontSize
                            words=word list
                                each word is itself a fragment with
                                various settings

        This structure can be used to easily draw paragraphs with the various alignments.
        You can supply either a single width or a list of widths; the latter will have its
        last item repeated until necessary. A 2-element list is useful when there is a
        different first line indent; a longer list could be created to facilitate custom wraps
        around irregular objects."""

        if type(width) <> ListType: maxWidths = [width]
        else: maxWidths = width
        lines = []
        lineno = 0
        style = self.style
        fFontSize = float(style.fontSize)
        if style.hyphenation:
            hyphenator = hyphRegistry.get(style.language,None)
        else: # Keine Silbentrennung aktiv
            hyphenator = None

        #for bullets, work out width and ensure we wrap the right amount onto line one
        _handleBulletWidth(self.bulletText,style,maxWidths)

        def getMaxWidth(lineno):
            try:
                return maxWidths[lineno]
            except IndexError:
                return maxWidths[-1]  # use the last one

        maxWidth = maxWidths[lineno]
        #print "maxWidth",maxWidth

        self.height = 0
        autoLeading = getattr(self,'autoLeading',getattr(style,'autoLeading',''))
        calcBounds = autoLeading not in ('','off')
        frags = self.frags
        nFrags= len(frags)
        #HVB20070106 von RL 2.1
        if nFrags==1 and not hasattr(frags[0],'cbDefn'):
            f = frags[0]
            fontSize = f.fontSize
            fontName = f.fontName
            ascent, descent = getAscentDescent(fontName,fontSize)
            words = hasattr(f,'text') and split(f.text, ' ') or f.words
            spaceWidth = stringWidth(' ', fontName, fontSize, self.encoding)
            cLine = []
            currentWidth = - spaceWidth   # hack to get around extra space for word 1
            for windx,word in enumerate(words):
              # TryAgain
              tryAgain = True
              while tryAgain:
                tryAgain = False
                wordStr = word
                if isinstance(word,HyphenatedWord):
                    wordStr = word #HVB20060907 muss hier auf UTF8 geachtet werden?
                wordWidth = stringWidth(wordStr, fontName, fontSize, self.encoding)
                    
                newWidth = currentWidth + spaceWidth + wordWidth
                if newWidth <= maxWidth: #  or not len(cLine):
                    # fit one more on this line
                    cLine.append(wordStr)
                    currentWidth = newWidth
                else:
                    (action,left,right,spaceWasted) = self.findBestSolution(cLine,word,currentWidth,maxWidth,spaceWidth,fontName,fontSize,windx<len(words))
                    if action is self.OVERFLOW:
                        pass
                    elif action is self.SQUEEZE:
                        #print "SQUEEZE: %s %s" % (cLine,left)
                        cLine.append(left)
                        currentWidth = maxWidth
                    else:
                        assert action == self.HYPHENATE
                        #print "left=%r word=%r" % (left, word)
                        cLine.append(left)
                        currentWidth = maxWidth-spaceWasted
                    if currentWidth > self.width: self.width = currentWidth
                    lines.append((spaceWasted, cLine))
                    cLine = []
                    currentWidth = - spaceWidth
                    lineno += 1
                    maxWidth = getMaxWidth(lineno)
                    word = right
                    if word:
                        tryAgain = True

            #deal with any leftovers on the final line
            if cLine!=[]:
                #print "final line"
                # FIXME: replace Hyphenated words with strings again
                if currentWidth > self.width: self.width = currentWidth
                lines.append((maxWidth - currentWidth, cLine))

            return f.clone(kind=0, lines=lines,ascent=ascent,descent=descent,fontSize=fontSize)
        elif nFrags<=0:
            return ParaLines(kind=0, fontSize=style.fontSize, fontName=style.fontName,
                            textColor=style.textColor, lines=[])
        else:
            #if hasattr(self,'blPara'): #HVB20060907 RL20 sagt hier: and getattr(self,'_splitpara',0)
            if hasattr(self,'blPara') and getattr(self,'_splitpara',0): # HVB, 20071006 (von RL 2.1)
                #NB this is an utter hack that awaits the proper information
                #preserving splitting algorithm
                return self.blPara
            n = 0
            words = [] # HVB20071006 von RL 2.1
            for windx,w in enumerate(_getFragWords(frags)):
              f=w[-1][0]
              fontName = f.fontName
              fontSize = f.fontSize
              spaceWidth = stringWidth(' ',fontName, fontSize)
              
              # TODO Wo gehört maxSize = f.fontSize hin?
              
              tryAgain = True
              while tryAgain:
                # w is always representing one word.
                # w is a list where
                # w[0] is the width of the whole word
                # w[1] and so on are fragments of the word, one fragment for every style.
                #      Each fragment is a tuple (PFRAG, S) where PFRAG is a ParaFrag
                #      containing the style information (font, weight, size, color, ...)
                #      and s is the string with the fragment.
                # Example: The word "<b>it</b>alic"
                # w[0] = width of the word
                # w[1] = (ParaFrag(...bold=1,...), "it")
                # w[2] = (ParaFrag(...bold=0,...), "alic")
                # Caution: The last element of w can be a HyphenatedWord as well.
                tryAgain = False

                if not words:
                    currentWidth = -spaceWidth   # hack to get around extra space for word 1
                    maxSize = fontSize
                    maxAscent, minDescent = getAscentDescent(fontName,fontSize)

                wordWidth = w[0]
                f = w[1][0]
                if wordWidth>0:
                    newWidth = currentWidth + spaceWidth + wordWidth
                else:
                    newWidth = currentWidth
                # HVB20071006 von RL 2.1 BEGIN
                #test to see if this frag is a line break. If it is we will only act on it
                #if the current width is non-negative or the previous thing was a deliberate lineBreak
                lineBreak = hasattr(f,'lineBreak')
                #endLine = (newWidth>maxWidth and n>0) or lineBreak
                endLine = (newWidth>maxWidth) or lineBreak
                if not endLine:
                    if lineBreak: continue      #throw it away
                    nText = w[1][1]
                    if nText: n += 1
                    fontSize = f.fontSize
                    if calcBounds:
                        cbDefn = getattr(f,'cbDefn',None)
                        if getattr(cbDefn,'width',0):
                            descent,ascent = imgVRange(cbDefn.height,cbDefn.valign,fontSize)
                        else:
                            ascent, descent = getAscentDescent(f.fontName,fontSize)
                    else:
                        ascent, descent = getAscentDescent(f.fontName,fontSize)
                    maxSize = max(maxSize,fontSize)
                    maxAscent = max(maxAscent,ascent)
                    minDescent = min(minDescent,descent)
                    if not words:
                        g = f.clone()
                        words = [g]
                        g.text = nText
                    elif not _sameFrag(g,f):
                        if currentWidth>0 and ((nText!='' and nText[0]!=' ') or hasattr(f,'cbDefn')):
                            if hasattr(g,'cbDefn'):
                                i = len(words)-1
                                while i>=0:
                                    wi = words[i]
                                    cbDefn = getattr(wi,'cbDefn',None)
                                    if cbDefn:
                                        if not getattr(cbDefn,'width',0):
                                            i -= 1
                                            continue
                                    if not wi.text.endswith(' '):
                                        wi.text += ' '
                                    break
                            else:
                                if not g.text.endswith(' '):
                                    g.text += ' '
                        g = f.clone()
                        words.append(g)
                        g.text = nText
                    else:
                        if nText!='' and nText[0]!=' ':
                            g.text += ' ' + nText

                    if isinstance(w[-1],HyphenatedWord):
                        hyphWord = w.pop()
                        # and forget about it...
                    for i in w[2:]:
                        g = i[0].clone()
                        g.text=i[1]
                        words.append(g)
                        fontSize = g.fontSize
                        if calcBounds:
                            cbDefn = getattr(g,'cbDefn',None)
                            if getattr(cbDefn,'width',0):
                                descent,ascent = imgVRange(cbDefn.height,cbDefn.valign,fontSize)
                            else:
                                ascent, descent = getAscentDescent(g.fontName,fontSize)
                        else:
                            ascent, descent = getAscentDescent(g.fontName,fontSize)
                        maxSize = max(maxSize,fontSize)
                        maxAscent = max(maxAscent,ascent)
                        minDescent = min(minDescent,descent)
                    currentWidth = newWidth

                else:
                    # The next word (w) does not fit anymore
                    # HVB20071006 von RL 2.1 BEGIN
                    if lineBreak:
                        g = f.clone()
                        #del g.lineBreak
                        words.append(g)
                    # HVB20071006 von RL 2.1 END
                    # If we have hyphenated the word,
                    # than we have added the hyphenated word as the last element to the list w.
                    if isinstance(w[-1],HyphenatedWord):
                        hyphWord = w[-1]
                        wordstr = hyphWord
                    else:
                        wordstr = "".join([pfrag[1] for pfrag in w[1:]])
                        uniwordstr = wordstr.decode(self.encoding)
                        if hyphenator and uniwordstr:
                            hyphWord = hyphenator.hyphenate(uniwordstr)
                            # HVB, 29.04.2008
                            if hyphWord is None:
                                hyphWord = HyphenatedWord(uniwordstr, hyphenations=[])
                        else:
                            #if not uniwordstr:
                            #    print "TODO Leeres Wort ergibt sich aus pfrag[1] for pfrag in w[1:]]"
                            hyphWord = HyphenatedWord(uniwordstr, hyphenations=[])
                        #if self.debug and not hyphWord.hyphenations and hyphWord.info[0] != "NOT_HYPHENATABLE":
                        #    print "---- %s : %s" % (hyphWord.word,hyphWord.info)
                        w.append(hyphWord)

                    nFragments = len(w)-2 # w[0] is width, w[-1] the hyphWord
                    #print "word does not fit anymore => trying hyphenation algorithm."
                    #print "word '%s' has %d fragments." % (wordstr , nFragments)
                    #if nFragments>1: print "first fragment: %s" % w[1][1]

                    (action,left,right,spaceWasted) = self.findBestSolutionX(words,w,currentWidth,maxWidth,spaceWidth,windx<len(words))
                    #print "%s --> %s" % (wordstr,action)
                    if action is self.OVERFLOW:
                        pass
                    elif action is self.SQUEEZE:
                        #print "SQUEEZE: %s %s" % (cLine,left)
                        # cLine.append(left)
                        # fit one more on this line
                        n = n + 1
                        maxSize = max(maxSize,f.fontSize)
                        nText = left[1][1]
                        if words==[]:
                            g = f.clone()
                            words = [g]
                            g.text = nText
                        elif not _sameFrag(g,f):
                            if currentWidth>0 and ((nText!='' and nText[0]!=' ') or hasattr(f,'cbDefn')):
                                if hasattr(g,'cbDefn'):
                                    i = len(words)-1
                                    while hasattr(words[i],'cbDefn'): i = i-1
                                    words[i].text = words[i].text + ' '
                                else:
                                    g.text = g.text + ' '
                                #nSp = nSp + 1 HVB20071006 von RL 2.1
                            g = f.clone()
                            words.append(g)
                            g.text = nText
                        else:
                            if nText!='' and nText[0]!=' ':
                                g.text = g.text + ' ' + nText

                        if isinstance(w[-1],HyphenatedWord):
                            hyphWord = w.pop()
                            # and forget about it...
                        for i in left[2:]:
                            g = i[0].clone()
                            g.text=i[1]
                            words.append(g)
                            maxSize = max(maxSize,g.fontSize)
                        currentWidth = maxWidth
                    else:
                        assert action==self.HYPHENATE
                        #print "left", left[-1][1], "right", right[-1]
                        # cLine.append(left)
                        # fit one more on this line
                        n = n + 1
                        maxSize = max(maxSize,f.fontSize)
                        nText = left[1][1]
                        if words==[]:
                            g = f.clone()
                            words = [g]
                            g.text = nText
                        elif not _sameFrag(g,f):
                            if currentWidth>0 and ((nText!='' and nText[0]!=' ') or hasattr(f,'cbDefn')):
                                if hasattr(g,'cbDefn'):
                                    i = len(words)-1
                                    while hasattr(words[i],'cbDefn'): i = i-1
                                    words[i].text = words[i].text + ' '
                                else:
                                    g.text = g.text + ' '
                                #nSp += 1 HVB von RL 2.1
                            g = f.clone()
                            words.append(g)
                            g.text = nText
                        else:
                            if nText!='' and nText[0]!=' ':
                                g.text = g.text + ' ' + nText

                        for i in left[2:]:
                            g = i[0].clone()
                            g.text=i[1]
                            words.append(g)
                            maxSize = max(maxSize,g.fontSize)
                        currentWidth = maxWidth-spaceWasted
                    if currentWidth>self.width: self.width = currentWidth
                    #lines.append((spaceWasted, cLine))
                    lines.append(FragLine(extraSpace=spaceWasted,wordCount=n,
                                  lineBreak=lineBreak, words=words, fontSize=maxSize, ascent=maxAscent, descent=minDescent))
                    words = []
                    currentWidth = - spaceWidth
                    lineno += 1
                    maxWidth = getMaxWidth(lineno)
                    # HVB20071006 von RL 2.1 BEGIN
                    if lineBreak:
                        n = 0
                        words = []
                        continue
                    # HVB20071006 von RL 2.1 END
                    maxSize = 0
                    n = 0
                    w = right
                    if w:
                        tryAgain = True
                        #print "              TryAgain!, w=%s" % (HVBDBG.s(w))

            #deal with any leftovers on the final line
            if words!=[]:
                if currentWidth>self.width: self.width = currentWidth
                lines.append(FragLine(extraSpace=(maxWidth - currentWidth),wordCount=n,
                                    words=words, fontSize=maxSize, ascent=maxAscent, descent=minDescent))
            return ParaLines(kind=1, lines=lines)

        return lines


    # this routine is copied from the original (just because we are using "join" here).
    def breakLinesCJK(self, width):
        """Initially, the dumbest possible wrapping algorithm.
        Cannot handle font variations."""

        style = self.style
        #for now we only handle one fragment.  Need to generalize this quickly.
        if len(self.frags) > 1:
            raise ValueError('CJK Wordwrap can only handle one fragment per paragraph for now.  Tried to handle:\ntext:  %s\nfrags: %s' % (self.text, self.frags))
        elif len(self.frags) == 0:
            return ParaLines(kind=0, fontSize=style.fontSize, fontName=style.fontName,
                            textColor=style.textColor, lines=[])
        f = self.frags[0]
        if 1 and hasattr(self,'blPara') and getattr(self,'_splitpara',0):
            #NB this is an utter hack that awaits the proper information
            #preserving splitting algorithm
            return f.clone(kind=0, lines=self.blPara.lines)
        if type(width)!=ListType: maxWidths = [width]
        else: maxWidths = width
        lines = []
        lineno = 0
        fFontSize = float(style.fontSize)

        #for bullets, work out width and ensure we wrap the right amount onto line one
        _handleBulletWidth(self.bulletText, style, maxWidths)

        maxWidth = maxWidths[0]

        self.height = 0

        f = self.frags[0]

        if hasattr(f,'text'):
            text = f.text
        else:
            text = ''.join(getattr(f,'words',[]))

        from reportlab.lib.textsplit import wordSplit
        lines = wordSplit(text, maxWidths[0], f.fontName, f.fontSize)
        #the paragraph drawing routine assumes multiple frags per line, so we need an
        #extra list like this
        #  [space, [text]]
        #
        wrappedLines = [(sp, [line]) for (sp, line) in lines]
        return f.clone(kind=0, lines=wrappedLines)


    # this routine is copied from the original (because it uses many _-functions)
    def drawPara(self,debug=0):
        """Draws a paragraph according to the given style.
        Returns the final y position at the bottom. Not safe for
        paragraphs without spaces e.g. Japanese; wrapping
        algorithm will go infinite."""

        #stash the key facts locally for speed
        canvas = self.canv
        style = self.style
        blPara = self.blPara
        lines = blPara.lines
        leading = style.leading
        autoLeading = getattr(self,'autoLeading',getattr(style,'autoLeading',''))

        #work out the origin for line 1
        leftIndent = style.leftIndent
        cur_x = leftIndent

        if debug:
            bw = 0.5
            bc = Color(1,1,0)
            bg = Color(0.9,0.9,0.9)
        else:
            bw = getattr(style,'borderWidth',None)
            bc = getattr(style,'borderColor',None)
            bg = style.backColor
        
        #if has a background or border, draw it
        if bg or (bc and bw):
            canvas.saveState()
            op = canvas.rect
            kwds = dict(fill=0,stroke=0)
            if bc and bw:
                canvas.setStrokeColor(bc)
                canvas.setLineWidth(bw)
                kwds['stroke'] = 1
                br = getattr(style,'borderRadius',0)
                if br and not debug:
                    op = canvas.roundRect
                    kwds['radius'] = br
            if bg:
                canvas.setFillColor(bg)
                kwds['fill'] = 1
            bp = getattr(style,'borderPadding',0)
            op(leftIndent-bp,
                        -bp,
                        self.width - (leftIndent+style.rightIndent)+2*bp,
                        self.height+2*bp,
                        **kwds)
            canvas.restoreState()

        nLines = len(lines)
        bulletText = self.bulletText
        if nLines > 0:
            _offsets = getattr(self,'_offsets',[0])
            _offsets += (nLines-len(_offsets))*[_offsets[-1]]
            canvas.saveState()
            #canvas.addLiteral('%% %s.drawPara' % _className(self))
            alignment = style.alignment
            offset = style.firstLineIndent+_offsets[0]
            lim = nLines-1
            noJustifyLast = not (hasattr(self,'_JustifyLast') and self._JustifyLast)

            if blPara.kind==0:
                if alignment == TA_LEFT:
                    dpl = _leftDrawParaLine
                elif alignment == TA_CENTER:
                    dpl = _centerDrawParaLine
                elif self.style.alignment == TA_RIGHT:
                    dpl = _rightDrawParaLine
                elif self.style.alignment == TA_JUSTIFY:
                    dpl = _justifyDrawParaLine
                f = blPara
                cur_y = self.height - getattr(f,'ascent',f.fontSize)    #TODO fix XPreformatted to remove this hack
                if bulletText:
                    offset = _drawBullet(canvas,offset,cur_y,bulletText,style)

                #set up the font etc.
                canvas.setFillColor(f.textColor)

                tx = self.beginText(cur_x, cur_y)
                if autoLeading=='max':
                    leading = max(leading,1.2*f.fontSize)
                elif autoLeading=='min':
                    leading = 1.2*f.fontSize

                #now the font for the rest of the paragraph
                tx.setFont(f.fontName, f.fontSize, leading)
                ws = lines[0][0]
                t_off = dpl( tx, offset, ws, lines[0][1], noJustifyLast and nLines==1)
                if f.underline or f.link or f.strike:
                    xs = tx.XtraState = ABag()
                    xs.cur_y = cur_y
                    xs.f = f
                    xs.style = style
                    xs.lines = lines
                    xs.underlines=[]
                    xs.underlineColor=None
                    xs.strikes=[]
                    xs.strikeColor=None
                    xs.links=[]
                    xs.link=f.link
                    canvas.setStrokeColor(f.textColor)
                    dx = t_off+leftIndent
                    if dpl!=_justifyDrawParaLine: ws = 0
                    underline = f.underline or (f.link and platypus_link_underline)
                    strike = f.strike
                    link = f.link
                    if underline: _do_under_line(0, dx, ws, tx)
                    if strike: _do_under_line(0, dx, ws, tx, lm=0.125)
                    if link: _do_link_line(0, dx, ws, tx)

                    #now the middle of the paragraph, aligned with the left margin which is our origin.
                    for i in xrange(1, nLines):
                        ws = lines[i][0]
                        t_off = dpl( tx, _offsets[i], ws, lines[i][1], noJustifyLast and i==lim)
                        if dpl!=_justifyDrawParaLine: ws = 0
                        if underline: _do_under_line(i, t_off+leftIndent, ws, tx)
                        if strike: _do_under_line(i, t_off+leftIndent, ws, tx, lm=0.125)
                        if link: _do_link_line(i, t_off+leftIndent, ws, tx)
                else:
                    for i in xrange(1, nLines):
                        dpl( tx, _offsets[i], lines[i][0], lines[i][1], noJustifyLast and i==lim)
            else:
                f = lines[0]
                cur_y = self.height - getattr(f,'ascent',f.fontSize)    #TODO fix XPreformatted to remove this hack
                # default?
                dpl = _leftDrawParaLineX
                if bulletText:
                    oo = offset
                    offset = _drawBullet(canvas,offset,cur_y,bulletText,style)
                if alignment == TA_LEFT:
                    dpl = _leftDrawParaLineX
                elif alignment == TA_CENTER:
                    dpl = _centerDrawParaLineX
                elif self.style.alignment == TA_RIGHT:
                    dpl = _rightDrawParaLineX
                elif self.style.alignment == TA_JUSTIFY:
                    dpl = _justifyDrawParaLineX
                else:
                    raise ValueError("bad align %s" % repr(alignment))

                #set up the font etc.
                tx = self.beginText(cur_x, cur_y)
                xs = tx.XtraState=ABag()
                xs.textColor=None
                xs.rise=0
                xs.underline=0
                xs.underlines=[]
                xs.underlineColor=None
                xs.strike=0
                xs.strikes=[]
                xs.strikeColor=None
                xs.links=[]
                xs.link=None
                xs.leading = style.leading
                xs.leftIndent = leftIndent
                tx._leading = None
                tx._olb = None
                xs.cur_y = cur_y
                xs.f = f
                xs.style = style
                xs.autoLeading = autoLeading

                tx._fontname,tx._fontsize = None, None
                dpl( tx, offset, lines[0], noJustifyLast and nLines==1)
                _do_post_text(tx)

                #now the middle of the paragraph, aligned with the left margin which is our origin.
                for i in xrange(1, nLines):
                    f = lines[i]
                    dpl( tx, _offsets[i], f, noJustifyLast and i==lim)
                    _do_post_text(tx)

            canvas.drawText(tx)
            canvas.restoreState()

    # this routine is copied from the original (just because we are using "join" here).
    def getPlainText(self,identify=None):
        """Convenience function for templates which want access
        to the raw text, without XML tags. """
        frags = getattr(self,'frags',None)
        if frags:
            plains = []
            for frag in frags:
                if hasattr(frag, 'text'):
                    plains.append(frag.text)
            return myjoin(plains, '')
        elif identify:
            text = getattr(self,'text',None)
            if text is None: text = repr(self)
            return text
        else:
            return ''
