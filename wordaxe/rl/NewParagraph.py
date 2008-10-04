#!/bin/env/python
# -*- coding: utf-8 -*-

# Neue Paragraph-Implementierung

from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus.paraparser import ParaParser
from reportlab.platypus.flowables import Flowable
from reportlab.rl_config import platypus_link_underline 
import re
from copy import copy

import wordaxe
from wordaxe.hyphen import HyphenationPoint, SHY, HyphenatedWord, Hyphenator
from wordaxe.rl.para_fragments import *

pt = 1 # Points is the base unit in RL

# This is more or less copied from RL paragraph


def setXPos(tx,dx):
    if dx>1e-6 or dx<-1e-6:
        tx.setXPos(dx)


# This is more or less copied from RL paragraph

def imgVRange(h,va,fontSize):
    '''return bottom,top offsets relative to baseline(0)'''
    if va=='baseline':
        iyo = 0
    elif va in ('text-top','top'):
        iyo = fontSize-h
    elif va=='middle':
        iyo = fontSize - (1.2*fontSize+h)*0.5
    elif va in ('text-bottom','bottom'):
        iyo = fontSize - 1.2*fontSize
    elif va=='super':
        iyo = 0.5*fontSize
    elif va=='sub':
        iyo = -0.5*fontSize
    elif hasattr(va,'normalizedValue'):
        iyo = va.normalizedValue(fontSize)
    else:
        iyo = va
    return iyo,iyo+h

_56=5./6
_16=1./6
def _putFragLine(cur_x, tx, line):
    #print "_putFragLine", line
    assert isinstance(line, Line)
    xs = tx.XtraState
    cur_y = xs.cur_y
    #print "_putFragLine: xs.cur_y:", xs.cur_y
    x0 = tx._x0
    autoLeading = xs.autoLeading
    leading = xs.leading
    cur_x += xs.leftIndent
    dal = autoLeading in ('min','max')
    if dal:
        if autoLeading=='max':
            ascent = max(_56*leading,line.ascent)
            descent = max(_16*leading,-line.descent)
        else:
            ascent = line.ascent
            descent = -line.descent
        leading = ascent+descent
    if tx._leading!=leading:
        tx.setLeading(leading)
    if dal:
        olb = tx._olb
        if olb is not None:
            xcy = olb-ascent
            if tx._oleading!=leading:
                cur_y += leading - tx._oleading
            if abs(xcy-cur_y)>1e-8:
                cur_y = xcy
                tx.setTextOrigin(x0,cur_y)
                xs.cur_y = cur_y
        tx._olb = cur_y - descent
        tx._oleading = leading
    ws = getattr(tx,'_wordSpace',0)
    nSpaces = 0

    # Now join fragments with the same style again
    fragments = []
    for frag in line.iter_flattened_frags():
        if not fragments or not hasattr(frag,"text") or last_style is not frag.style:
            last_style = frag.style
            last_frag = copy(frag)
            fragments.append(last_frag)
        else:
            last_frag.text += frag.text
            last_frag.width += frag.width
        
    for frag in fragments:
        #print "render", frag
        f = frag.style
        if hasattr(f,'cbDefn'):
            cbDefn = f.cbDefn
            kind = cbDefn.kind
            if kind=='img':
                #draw image cbDefn,cur_y,cur_x
                w = cbDefn.width
                h = cbDefn.height
                txfs = tx._fontsize
                if txfs is None:
                    txfs = xs.style.fontSize
                iy0,iy1 = imgVRange(h,cbDefn.valign,txfs)
                cur_x_s = cur_x + nSpaces*ws
                tx._canvas.drawImage(cbDefn.image,cur_x_s,cur_y+iy0,w,h,mask='auto')
                cur_x += w
                cur_x_s += w
                setXPos(tx,cur_x_s-tx._x0)
            else:
                name = cbDefn.name
                if kind=='anchor':
                    tx._canvas.bookmarkHorizontal(name,cur_x,cur_y+leading)
                else:
                    func = getattr(tx._canvas,name,None)
                    if not func:
                        raise AttributeError("Missing %s callback attribute '%s'" % (kind,name))
                    func(tx._canvas,kind,cbDefn.label)
            if f is words[-1]:
                if not tx._fontname:
                    tx.setFont(xs.style.fontName,xs.style.fontSize)
                    tx._textOut('',1)
                elif kind=='img':
                    tx._textOut('',1)
        else:
            cur_x_s = cur_x + nSpaces*ws
            if (tx._fontname,tx._fontsize)!=(f.fontName,f.fontSize):
                tx._setFont(f.fontName, f.fontSize)
            if xs.textColor!=f.textColor:
                xs.textColor = f.textColor
                tx.setFillColor(f.textColor)
            if xs.rise!=f.rise:
                xs.rise=f.rise
                tx.setRise(f.rise)
            text = frag.text
            tx._textOut(text,frag is fragments[-1])    # cheap textOut
            if not xs.underline and f.underline:
                xs.underline = 1
                xs.underline_x = cur_x_s
                xs.underlineColor = f.textColor
            elif xs.underline:
                if not f.underline:
                    xs.underline = 0
                    xs.underlines.append( (xs.underline_x, cur_x_s, xs.underlineColor) )
                    xs.underlineColor = None
                elif xs.textColor!=xs.underlineColor:
                    xs.underlines.append( (xs.underline_x, cur_x_s, xs.underlineColor) )
                    xs.underlineColor = xs.textColor
                    xs.underline_x = cur_x_s
            if not xs.strike and f.strike:
                xs.strike = 1
                xs.strike_x = cur_x_s
                xs.strikeColor = f.textColor
            elif xs.strike:
                if not f.strike:
                    xs.strike = 0
                    xs.strikes.append( (xs.strike_x, cur_x_s, xs.strikeColor) )
                    xs.strikeColor = None
                elif xs.textColor!=xs.strikeColor:
                    xs.strikes.append( (xs.strike_x, cur_x_s, xs.strikeColor) )
                    xs.strikeColor = xs.textColor
                    xs.strike_x = cur_x_s
            if f.link and not xs.link:
                if not xs.link:
                    xs.link = f.link
                    xs.link_x = cur_x_s
                    xs.linkColor = xs.textColor
            elif xs.link:
                if not f.link:
                    xs.links.append( (xs.link_x, cur_x_s, xs.link, xs.linkColor) )
                    xs.link = None
                    xs.linkColor = None
                elif f.link!=xs.link or xs.textColor!=xs.linkColor:
                    xs.links.append( (xs.link_x, cur_x_s, xs.link, xs.linkColor) )
                    xs.link = f.link
                    xs.link_x = cur_x_s
                    xs.linkColor = xs.textColor
            txtlen = tx._canvas.stringWidth(text, tx._fontname, tx._fontsize)
            # TODO wir haben doch die TExtlänge schon!
            cur_x += txtlen
            nSpaces += text.count(' ')
    cur_x_s = cur_x+(nSpaces-1)*ws
    if xs.underline:
        xs.underlines.append( (xs.underline_x, cur_x_s, xs.underlineColor) )
    if xs.strike:
        xs.strikes.append( (xs.strike_x, cur_x_s, xs.strikeColor) )
    if xs.link:
        xs.links.append( (xs.link_x, cur_x_s, xs.link,xs.linkColor) )
    if tx._x0!=x0:
        setXPos(tx,x0-tx._x0)

def _drawBullet(canvas, offset, cur_y, bulletText, style):
    '''draw a bullet text could be a simple string or a frag list'''
    tx2 = canvas.beginText(style.bulletIndent, cur_y+getattr(style,"bulletOffsetY",0))
    tx2.setFont(style.bulletFontName, style.bulletFontSize)
    tx2.setFillColor(hasattr(style,'bulletColor') and style.bulletColor or style.textColor)
    if isinstance(bulletText,basestring):
        tx2.textOut(bulletText)
    else:
        for f in bulletText:
            tx2.setFont(f.fontName, f.fontSize)
            tx2.setFillColor(f.textColor)
            tx2.textOut(f.text)

    canvas.drawText(tx2)
    #AR making definition lists a bit less ugly
    #bulletEnd = tx2.getX()
    bulletEnd = tx2.getX() + style.bulletFontSize * 0.6
    offset = max(offset,bulletEnd - style.leftIndent)
    return offset

def _handleBulletWidth(bulletText, style, max_widths):
    '''work out bullet width and adjust max_widths[0] if neccessary
    '''
    if bulletText:
        if isinstance(bulletText,basestring):
            bulletWidth = pdfmetrics.stringWidth( bulletText, style.bulletFontName, style.bulletFontSize)
        else:
            #it's a list of fragments
            bulletWidth = 0
            for f in bulletText:
                bulletWidth = bulletWidth + pdfmetrics.stringWidth(f.text, f.fontName, f.fontSize)
        bulletRight = style.bulletIndent + bulletWidth + 0.6 * style.bulletFontSize
        indent = style.leftIndent+style.firstLineIndent
        if bulletRight > indent:
            #..then it overruns, and we have less space available on line 1
            max_widths[0] -= (bulletRight - indent)

_scheme_re = re.compile('^[a-zA-Z][-+a-zA-Z0-9]+$')
def _doLink(tx,link,rect):
    if isinstance(link,unicode):
        link = link.encode('utf8')
    parts = link.split(':',1)
    scheme = len(parts)==2 and parts[0].lower() or ''
    if _scheme_re.match(scheme) and scheme!='document':
        kind=scheme.lower()=='pdf' and 'GoToR' or 'URI'
        if kind=='GoToR': link = parts[1]
        tx._canvas.linkURL(link, rect, relative=1, kind=kind)
    else:
        if link[0]=='#':
            link = link[1:]
            scheme=''
        tx._canvas.linkRect("", scheme!='document' and link or parts[1], rect, relative=1)

def _do_post_text(tx):

    xs = tx.XtraState
    leading = xs.style.leading
    autoLeading = xs.autoLeading

    if True:
        f = xs.f
        if autoLeading=='max':
            leading = max(leading,1.2*f.fontSize)
        elif autoLeading=='min':
            leading = 1.2*f.fontSize
        ff = 0.125*f.fontSize
        y0 = xs.cur_y
        y = y0 - ff
        csc = None
        for x1,x2,c in xs.underlines:
            if c!=csc:
                tx._canvas.setStrokeColor(c)
                csc = c
            tx._canvas.line(x1, y, x2, y)
        xs.underlines = []
        xs.underline=0
        xs.underlineColor=None

        ys = y0 + 2*ff
        for x1,x2,c in xs.strikes:
            if c!=csc:
                tx._canvas.setStrokeColor(c)
                csc = c
            tx._canvas.line(x1, ys, x2, ys)
        xs.strikes = []
        xs.strike=0
        xs.strikeColor=None

        yl = y + leading
        for x1,x2,link,c in xs.links:
            if platypus_link_underline:
                if c!=csc:
                    tx._canvas.setStrokeColor(c)
                    csc = c
                tx._canvas.line(x1, y, x2, y)
            _doLink(tx, link, (x1, y, x2, yl))
    xs.links = []
    xs.link=None
    xs.linkColor=None
    #print "leading:", leading
    xs.cur_y -= leading
    #print "xs.cur_y:", xs.cur_y
    

def textTransformFrags(frags,style):
    tt = style.textTransform
    if tt:
        tt=tt.lower()
        if tt=='lowercase':
            tt = unicode.lower
        elif tt=='uppercase':
            tt = unicode.upper
        elif  tt=='capitalize':
            tt = unicode.title
        elif tt=='none':
            return
        else:
            raise ValueError('ParaStyle.textTransform value %r is invalid' % style.textTransform) 
        n = len(frags)
        if n==1:
            #single fragment the easy case
            frags[0].text = tt(frags[0].text)
        elif tt is unicode.title:
            pb = True
            for f in frags:
                t = f.text
                if not t: continue
                u = t
                if u.startswith(u' ') or pb:
                    u = tt(u)
                else:
                    i = u.find(u' ')
                    if i>=0:
                        u = u[:i]+tt(u[i:])
                pb = u.endswith(u' ')
                f.text = u
        else:
            for f in frags:
                t = f.text
                if not t: continue
                f.text = tt(t)
    

# Here follows a clean(er) paragraph implemention
    
class Paragraph(Flowable):
    "A simple new implementation for Paragraph flowables."
    
    def __init__(self, text, style, bulletText = None, frags=None, lines=None, caseSensitive=1, encoding='utf-8', keepWhiteSpace=False):
        """
        Either text and style or frags must be supplied.
        """
        self.caseSensitive = caseSensitive
        self.style = style
        self.bulletText = bulletText
        self.keepWhiteSpace = keepWhiteSpace # TODO: Unterstützen
        
        if text is None:
            assert frags is not None or lines is not None
            if frags is not None:
                #print id(self), "init with frags", frags
                for frag in frags: assert isinstance(frag, Fragment)
                self.frags = frags
            else:
                #print id(self), "init with %d lines" % len(lines)
                for line in lines: assert isinstance(line, Line)
                self._lines = lines
        else:
            #print id(self), "init with text"
            assert isinstance(text, basestring)
            # Text parsen
            if not isinstance(text, unicode):
                text = unicode(text, encoding)
            self.frags = list(self.parse(text, style, bulletText))

    def parse_tokens(self, text, style, bulletText):
        "Use the ParaParser to create a sequence of fragments"
        parser = ParaParser()
        style1, fragList, bFragList = parser.parse(text, style)
        for f in fragList:
            if getattr(f, "lineBreak", False):
                assert not f.text
                yield StyledNewLine(f)
            text = f.text
            del f.text
            if not isinstance(text, unicode):
                text = unicode(text, "utf-8")
            while u" " in text:
                indxSpace = text.find(u" ")
                if indxSpace > 0:
                    yield StyledText(text[:indxSpace], f)
                indxNext = indxSpace
                while text[indxNext:].startswith(u" "):
                    indxNext += 1
                yield StyledSpace(f) # we ignore repeated blanks
                text = text[indxNext:]
            if text:
                yield StyledText(text, f)

    def parse(self, text, style, bulletText):
        """
        Use the ParaParser to create a list of words.
        Yields StyledWords, StyledSpace and other entries,
        but StyledTexts are grouped to StyledWords.
        """
        wordFrags = []
        for frag in self.parse_tokens(text, style, bulletText):
            if isinstance(frag, StyledText):
                wordFrags.append(frag)
            else:
                if wordFrags:
                    yield StyledWord(wordFrags)
                    wordFrags = []
                yield frag
        if wordFrags:
            yield StyledWord(wordFrags)
        
    def __repr__(self):
        return "%s(frags=%r)" % (self.__class__.__name__, self.frags)

    def calcLineHeight(self, line):
        """
        Compute the height needed for a given line.
        """
        #print "calcLineHeight", self.style.leading
        return self.style.leading
        # TODO aus frags berechnen?
    
    def wrap(self, availW, availH):
        """
        """
        #print id(self), "wrap", availW, availH
        if hasattr(self, "_lines"):
            height = sum([line.height for line in self._lines])
            assert height <= availH + 1e-5
            return availW, height
        else:
            return self.i_wrap(availW, availH)
            
    def i_wrap(self, availW, availH):
        """
        Return the height and width that are actually needed.
        Note:
        This will abort if the text does not fit entirely.
        The lines measured so far will be stored in a private
        attribute _lines (to improve performance).
        TODO: Should StyledSpaces be ignored before or after StyledNewLines?
        """
        #print id(self), "i_wrap", availW, availH
        lines = []          # lines so far
        sumHeight = 0       # sum of lines heights so far
        lineHeight = 0      # height of current line
        width = 0           # width of current line
        lineFrags = []      # (flattened) fragments in current line
        
        style = self.style
        leftIndent = style.leftIndent
        first_line_width = availW - (leftIndent+style.firstLineIndent) - style.rightIndent
        later_widths = availW - leftIndent - style.rightIndent
        max_widths = [first_line_width, later_widths]
        
        _handleBulletWidth(self.bulletText,style,max_widths)
        
        def iter_widths(max_widths=max_widths):
            # an iterator that repeats the last element infinitely
            for w in max_widths: yield w
            while True: yield w
        width_iter = iter_widths()
        max_width = width_iter.next()

        for indx, frag in enumerate(self.frags):
            if sumHeight > availH:
                break
            action = "ADD"
            w = 0
            if isinstance(frag, StyledNewLine):
                action = "LINEFEED,IGNORE"
            elif hasattr(frag, "width"):
                w = frag.width
                if width + w > max_width:
                    # does not fit
                    #print "does not fit:", frag, width, w, max_width
                    if isinstance(frag, StyledWord):
                        # Hyphenation support
                        act, left, right, spaceWasted \
                            = self.findBestSolution(lineFrags, frag, max_width-width, True)
                        # TODO: vorerst immer mit try_squeeze
                        if act == self.OVERFLOW:
                            action = "LINEFEED,ADD"
                        elif act == self.SQUEEZE:
                            action = "ADD,LINEFEED"
                        elif act == self.HYPHENATE:
                            action = "ADD_L,LINEFEED,ADD_R"
                        else:
                            raise AssertionError
                    else:
                        action = "LINEFEED,ADD"
            else:
                # Some Meta Fragment
                pass
            for act in action.split(","):
                if act == "LINEFEED":
                    #print act, 
                    lineHeight = self.style.leading # TODO correct height calculation
                    #print lineHeight, 
                    baseline = 0   # TODO correct baseline calculation
                    line = Line(lineFrags, width, lineHeight, baseline, max_width - width, self.keepWhiteSpace)
                    lines.append(line)
                    lineFrags = []
                    width = 0
                    max_width = width_iter.next()
                    sumHeight += lineHeight
                    #print sumHeight
                elif act == "IGNORE":
                    pass
                elif act == "ADD":
                    lineFrags.append(frag)
                    width += getattr(frag, "width", 0)
                elif act == "ADD_L":
                    lineFrags.append(left)
                    width += getattr(left, "width", 0)
                elif act == "ADD_R":
                    lineFrags.append(right)
                    width += getattr(right, "width", 0)
                else:
                    raise AssertionError
        else:
            # Everything did fit
            lineHeight = self.calcLineHeight(lineFrags)
            baseline = 0   # TODO correct baseline calculation
            line = Line(lineFrags, width, lineHeight, baseline, max_width - width, self.keepWhiteSpace)
            lines.append(line)
            lineFrags = []
            width = 0
            sumHeight += lineHeight            

        if sumHeight > availH:
            #print id(self), "doesn't fit"
            # don't store the last line (it does not fit)
            # TODO muss hier evtl. noch ein Linefeed dazwischen?
            #                        v
            self._unused = lines[-1].fragments + lineFrags + self.frags[indx:]
            self._lines = lines[:-1]
        else:
            #print id(self), "fits"
            self._unused = []
            self._lines = lines
        self._width = availW
        return availW, sumHeight

    def split(self, availWidth, availHeight):
        """
        Split the paragraph into two
        """
        print id(self), "split"
        
        if not hasattr(self, "_lines"):
            # This can only happen when split has been called
            # without a previous wrap for this Paragraph.
            # From looking at doctemplate.py and frames.py,
            # I assume this is only the case if the free space
            # in the frame is not even enough for getSpaceBefore.
            # Thus we can safely return []
            return []
        
        assert hasattr(self, "_unused")
        if len(self._lines) < 1: # minimum widow rows
            # Put everything on the next frame
            assert hasattr(self, "frags")
            del self._unused
            del self._lines
            return []
        elif not self._unused:
            # Everything fits on this page
            return [self]
        else:
            style = self.style
            # height/leading computation
            autoLeading = getattr(self,'autoLeading',getattr(style,'autoLeading',''))
            leading = style.leading
            if autoLeading not in ('','off'):
                s = height = 0
                if autoLeading=='max':
                    for i,l in enumerate(self._lines):
                        h = max(l.ascent-l.descent,leading)
                        n = height+h
                        if n>availHeight+1e-8:
                            break
                        height = n
                        s = i+1
                elif autoLeading=='min':
                    for i,l in enumerate(self._lines):
                        n = height+l.ascent-l.descent
                        if n>availHeight+1e-8:
                            break
                        height = n
                        s = i+1
                else:
                    raise ValueError('invalid autoLeading value %r' % autoLeading)
            # Widows/orphans
            # TODO: this cannot work, since we have not yet computed
            # the lines for the second part.
            n = len(self._lines)
            allowWidows = getattr(self,'allowWidows',getattr(self,'allowWidows',1))
            allowOrphans = getattr(self,'allowOrphans',getattr(self,'allowOrphans',0))
            if not allowOrphans:
                if s<=1:    #orphan?
                    del self._lines
                    del self._unused 
                    return []
            if n<=s:
                return [self]
            if not allowWidows:
                if n==s+1: #widow?
                    if (allowOrphans and n==3) or n>3:
                        s -= 1  #give the widow some company
                    else:
                        #no room for adjustment; force the whole para onwards
                        del self._lines
                        del self._unused 
                        return []
            first = self.__class__(text=None, style=self.style, bulletText=self.bulletText, lines=self._lines)
            first._width = self._width # TODO 20080911
            first._JustifyLast = 1
            if style.firstLineIndent != 0:
                style = deepcopy(style)
                style.firstLineIndent = 0
            second = self.__class__(text=None, style=self.style, bulletText=None, frags=self._unused)
            return [first, second]
            

    def beginText(self, x, y):
        return self.canv.beginText(x, y)

    def draw(self, debug=0):
        """
        Draw the paragraph.
        """
        #print id(self), "draw"

        # Code more or less copied from RL

        """Draws a paragraph according to the given style.
        Returns the final y position at the bottom. Not safe for
        paragraphs without spaces e.g. Japanese; wrapping
        algorithm will go infinite."""

        #stash the key facts locally for speed
        canvas = self.canv
        style = self.style
        lines = self._lines
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

        #print "Lines: %s" % lines
        nLines = len(lines)
        #print "len(lines)", nLines
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
            f = lines[0]
            #cur_y = self.height - getattr(f,'ascent',f.fontSize)
            cur_y = sum([line.height for line in lines]) - f.ascent
               
            # default?
            dpl = self._leftDrawParaLineX
            if bulletText:
                oo = offset
                offset = _drawBullet(canvas,offset,cur_y,bulletText,style)
            if alignment == TA_LEFT:
                dpl = self._leftDrawParaLineX
            elif alignment == TA_CENTER:
                dpl = self._centerDrawParaLineX
            elif self.style.alignment == TA_RIGHT:
                dpl = self._rightDrawParaLineX
            elif self.style.alignment == TA_JUSTIFY:
                dpl = self._justifyDrawParaLineX
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
        
    def _leftDrawParaLineX( self, tx, offset, line, last=0):
        # TODO 20080911 ist eher unsinnig! Die Breite des Absatzes kann ja im Verlauf schwanken,
        # z.B. wenn der Absatz um ein Bild herumfließen soll
        if line.space_wasted < 0: 
            return self._justifyDrawParaLineX(tx,offset,line,last)
        setXPos(tx,offset)
        _putFragLine(offset, tx, line)
        setXPos(tx,-offset)

    def _rightDrawParaLineX( self, tx, offset, line, last=0):
        # s.o.
        if line.space_wasted < 0: 
            return self._justifyDrawParaLineX(tx,offset,line,last)
        m = offset + line.space_wasted
        setXPos(tx,m)
        _putFragLine(m, tx, line)
        setXPos(tx,-m)

    def _centerDrawParaLineX( self, tx, offset, line, last=0):
        # s.o.
        if line.space_wasted < 0: 
            return self._justifyDrawParaLineX(tx,offset,line,last)
        m = offset + 0.5 * line.space_wasted
        setXPos(tx, m)
        _putFragLine(m, tx, line)
        setXPos(tx,-m)
        
    def _justifyDrawParaLineX( self, tx, offset, line, last=0):
        # s.o.
        setXPos(tx,offset)
        frags = line.fragments
        nSpaces = sum([len(frag.text) for frag in frags if isinstance(frag, StyledSpace)])
        if last or not nSpaces or abs(line.space_wasted)<=1e-8 or isinstance(frags[-1], StyledNewLine):
            _putFragLine(offset, tx, line)  #no space modification
        else:
            tx.setWordSpace(line.space_wasted / float(nSpaces))
            _putFragLine(offset, tx, line)
            tx.setWordSpace(0)
        setXPos(tx,-offset)
        
    class OVERFLOW:
         pass
    class SQUEEZE:
         pass
    class HYPHENATE:
         pass

    def rateHyph(self,base_penalty,frags,word,space_remaining):
        """Rate a possible hyphenation point"""
        #### EVTL ist Bewertung falsch, vor allem falls space_remaining ZU klein ist!
        #print "rateHyph %s %d" % (frags,space_remaining)

        spaces_width = sum([frag.width for frag in frags if isinstance(frag, StyledSpace)])
        if spaces_width:
            stretch = space_remaining/spaces_width
            if stretch<0:
                stretch_penalty = stretch*stretch*stretch*stretch*5000
            else:
                stretch_penalty = stretch*stretch*30
        else: # HVB 20060907: Kein einziges Wort?
            if space_remaining>0:
                 # TODO this should be easier
                 lst = [(len(frag.text), frag,width) for frag in frags if hasattr(frag,"text")]
                 sum_len = sum([x[0] for x in lst])
                 sum_width=sum([x[1] for x in lst])
                 avg_char_width = sum_width / sum_len
                 stretch_penalty = space_remaining/avg_char_width*20
            else:
                 stretch_penalty = 20000
        rating = 16384 - base_penalty - stretch_penalty
        return rating
        
    # finding bestSolution where the word uses possibly several different font styles
    # (action,left,right,spaceWasted) = self.findBestSolution(frags,w,currentWidth,maxWidth,windx<len(words))
    def findBestSolution(self, frags, word, space_remaining, try_squeeze):
        if self.style.hyphenation:
            hyphenator = wordaxe.hyphRegistry.get(self.style.language,None)
        else: # Keine Silbentrennung aktiv
            hyphenator = None
        assert isinstance(word, StyledWord)
        assert space_remaining <= word.width
            
        #print "findBestSolution %s %s %s" % (frags, word, space_remaining)
        nwords = len([True for frag in frags if isinstance(frag,StyledWord)])
        #print "nwords=%d" % nwords
        if hyphenator is None:
            # The old RL way: at least one word per line
            if nwords:
                #FALSCH return (self.OVERFLOW, word, 0, "", maxWidth-currentWidth)
                return (self.OVERFLOW, None, word, space_remaining)
            else:
                return (self.SQUEEZE, word, None, space_remaining - word.width)
        if not isinstance(word.text, HyphenatedWord):
            hw = hyphenator.hyphenate(word.text)
            if not hw: hw = HyphenatedWord(word.text, hyphenations=list())
            word.text = hw
        assert isinstance(word.text, HyphenatedWord)
        #print "hyphenations:", word.text.hyphenations

        # try OVERFLOW
        quality = self.rateHyph(0, frags, None, space_remaining)
        bestSolution = (self.OVERFLOW, None, word, space_remaining)
        #print "OV"
        # try SQUEEZE
        if try_squeeze and nwords: # HVB 20080925 warum "and nwords"?
            q = self.rateHyph(0, frags, word, space_remaining - word.width)
            if q>quality:
                #print "SQZ"
                bestSolution = (self.SQUEEZE, word, None, space_remaining - word.width)
                quality = q
        # try HYPHENATE
        for hp in word.text.hyphenations:
            left,right = word.splitAt(hp)
            #print "left=%r  right=%r" % (left, right)
            q = self.rateHyph(100-10*hp.quality,frags,left,space_remaining - left.width)
            if q>quality:
                bestSolution = (self.HYPHENATE, left, right, space_remaining - left.width)
                quality = q
        if bestSolution[0] is self.OVERFLOW and not nwords:
            # We have to make a hard break in the word
            #print "FORCE Hyphenation"
            # force at least a single character into this line
            left, right = word.splitAt(HyphenationPoint(1,1,0,"",0,""))
            bestSolution = (self.HYPHENATE, left, right, 0)
            for p in range(1,len(word.text)):
                if hyphWord.text[p-1] not in ["-",SHY]:
                    r= SHY
                else:
                    r = ""
                left,right = word.splitAt(HyphenationPoint(p,1,0,r,0,""))
                if left.width <= space_remaining:
                    bestSolution = (self.HYPHENATE, left, right, space_remaining - left.width)
                else:
                    # does not fit anymore
                    break

        #print "bestSolution:", HVBDBG.s(bestSolution)
        return bestSolution

# from here on, only test code...

if __name__ == "__main__":

    class HVBDBG:
        @staticmethod
        def s(obj):
            if type(obj) == list:
                return "[" + ", ".join([HVBDBG.s(x) for x in obj]) + "]"
            elif type(obj) == tuple:
                return "(" + ", ".join([HVBDBG.s(x) for x in obj]) + ")"
            elif isinstance(obj, ABag):
                return "ABag(.text=%r)" % obj.text
            elif type(obj) == float:
                return "%1.2f" % obj
            else:
                return repr(obj)


    # Test
    import styles
    styleSheet = styles.getSampleStyleSheet()
    style = styleSheet["Normal"]
    text = "Der blau<b>e </b><br />Klaus"
    p = Paragraph(text, style)
    print "width=%f" % sum([f.width for f in p.frags if hasattr(f,"width")])
    print "p=%r" % p
    
    import os
    import sys
    import unittest

    from reportlab.lib.units import cm
    from reportlab.lib import pagesizes
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate

    USE_HYPHENATION = True

    if USE_HYPHENATION:
        try:
            import wordaxe.rl.styles
            from wordaxe.DCWHyphenator import DCWHyphenator
            wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
        except SyntaxError:
            print "could not import hyphenation - try to continue WITHOUT hyphenation!"

    PAGESIZE = pagesizes.landscape(pagesizes.A4)

    class TwoColumnDocTemplate(BaseDocTemplate):
        "Define a simple, two column document."

        def __init__(self, filename, **kw):
            m = 2*cm
            cw, ch = (PAGESIZE[0]-2*m)/2., (PAGESIZE[1]-2*m)
            f1 = Frame(m, m+0.5*cm, cw-0.75*cm, ch-1*cm, id='F1', 
                leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
                showBoundary=True
            )
            f2 = Frame(cw+2.7*cm, m+0.5*cm, cw-0.75*cm, ch-1*cm, id='F2', 
                leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0,
                showBoundary=True
            )
            apply(BaseDocTemplate.__init__, (self, filename), kw)
            template = PageTemplate('template', [f1, f2])
            self.addPageTemplates(template)

    def test():    
        from reportlab.platypus.paragraph import Paragraph as platypus_Paragraph
        from wordaxe.DCWHyphenator import DCWHyphenator
        wordaxe.hyphRegistry["DE"] = DCWHyphenator("DE")
        stylesheet = getSampleStyleSheet()
        for indx, klass in enumerate([Paragraph, platypus_Paragraph]):
            normal = stylesheet['BodyText']
            normal.fontName = "Helvetica"
            normal.fontSize = 12
            normal.leading = 16
            if klass is Paragraph:
                normal.language = 'DE'
                normal.hyphenation = True
            normal.alignment = TA_JUSTIFY
            normal.firstLineIndent = 15*pt
            normal.leftIndent = 20*pt

            text = """Bedauerlicherweise ist ein <u>Donau</u>dampfschiffkapitän auch nur ein <a href="http://www.reportlab.org">Dampfschiff</a>kapitän."""
            # strange behaviour when next line uncommented
            text = " ".join(['<font color="red">%s</font>' % w for w in text.split()])

            text="""Das jeweils aktuelle Release der Software kann aber von der entsprechenden
    SourceForge <a color="blue" backColor="yellow" href="http://sourceforge.net/project/showfiles.php?group_id=105867">Download-Seite</a>
    heruntergeladen werden. Die allerneueste in Entwicklung befindliche Version
    wird im Sourceforge Subversion-Repository verwaltet.
    """.replace("\n"," ")

            story = []
            story.append(Paragraph(text, style=normal))
            story.append(klass(u"Eine Aufzählung, bei der der Text hoffentlich etwas länger als eine Zeile ist.", style=normal, bulletText="\xe2\x80\xa2"))
            story.append(klass(u"Silbentrennungsverfahren helfen dabei, extrem lange Donaudampfschiffe in handliche Schiffchen aufzuteilen. " * 10, style=normal))
            #story.append(klass(u"Silbentrennungsverfahren helfen dabei, extrem lange Donaudampfschiffe in handliche Schiffchen aufzuteilen.", style=normal, bulletText="\xe2\x80\xa2"))
            doc = TwoColumnDocTemplate(("test_NewParagraph_%d.pdf" %indx), pagesize=PAGESIZE)
            doc.build(story)
    
    test()
    