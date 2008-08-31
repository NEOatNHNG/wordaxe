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
import sys
import logging
logging.basicConfig()
log = logging.getLogger("BaseHyphenator")
log.setLevel(logging.INFO)

from xml.sax.saxutils import escape,quoteattr
import codecs
from wordaxe.hyphen import *

class Stripper:
    """
    A helper class for stripping words.
    """
    STD_PREFIX_CHARS = u"""'"([{¿"""
    STD_SUFFIX_CHARS = u"""'')]}?!.,;:"""

    def __init__(self, prefix_chars=STD_PREFIX_CHARS, 
                       suffix_chars=STD_SUFFIX_CHARS):
        self.prefix_chars = prefix_chars
        self.suffix_chars = suffix_chars
    
    def strip(self, word):
        """
        Returns a tuple (prefix, base, postfix)
        such that word = prefix+base+postfix.
        """
        lenword = len(word)
        offs_l = 0
        offs_r = lenword
        while offs_l < lenword and word[offs_l] in self.prefix_chars:
            offs_l += 1
        while offs_r > offs_l and word[offs_r-1] in self.suffix_chars:
            offs_r -= 1
        return word[:offs_l], word[offs_l:offs_r], word[offs_r:]
        
    def apply_stripped(self, word, func, *args, **kwargs):
        """
        Apply a hyphenation function for a word,
        but strips prefix and suffix characters before.
        Afterwards, these are added again.
        """
        assert isinstance(word, unicode)
        prefix, base, suffix = self.strip(word)
        result = func(base, *args, **kwargs)
        if result is None:
            return None
        if isinstance(result, HyphenatedWord):
            if prefix:
                result = result.prepend(prefix)
            if suffix:
                result = result.append(suffix)
        else:
            result = prefix + result + suffix
        return result
        
# Test
assert Stripper().strip(u"(Wie denn?") == (u"(", u"Wie denn", u"?")


class BaseHyphenator(Hyphenator):
    """
    This hyphenator is the most basic hyphenator which should work for
    any language.
    It only hyphenates a word after one of the following characters:
    -   minus sign (45, '\x2D')
    .   dot (46, '\x2E') (depending on its position)
    _   underscore (95, '\x5F')
    ­   shy hyphenation character (173, '\xAD')
    """
    
    stripper = Stripper() # Mit den Standard-Einstellungen
    
    def hyph(self,word):
        "Internal worker function."
        hword = HyphenatedWord(word, hyphenations=[])
        # strip common prefix- and suffix-characters
        l = len(word)
        if l < self.minWordLength:
            return hword
        # @TODO better use a regular expression for number/date detection
        for p in range(1,l-1):
            if word[p] in ["-", self.shy]:
                hword.hyphenations.append(HyphenationPoint(p+1,9,0,u"",0,u""))
            elif word[p] in ".,":
                if word[p-1] in "-+0123456789" and p+1<l and word[p+1] in "-+0123456789":
                    # a number or a date
                    return hword
                elif l<=3 or (word[p]=="." and word[-1]=="."):
                    # an abbreviation, for example "i.e."
                    return hword
                else:
                    hword.hyphenations.append(HyphenationPoint(p+1,5,0,self.shy,0,u""))
            elif word[p] in "_":
                hword.hyphenations.append(HyphenationPoint(p+1,5,0,self.shy,0,u""))
        if hword.hyphenations:
            return hword
        return None # unknown
        
    def i_hyphenate(self,aWord):
        assert isinstance(aWord, unicode)
        return self.stripper.apply_stripped(aWord, self.hyph)

    def learn(self,wordlist,htmlFile=None,VERBOSE=False):
        #print sys.stdout.encoding
        #print "VERBOSE:", VERBOSE
        cntWords = 0
        cntOK = 0
        unknownWords = []
        cntTooShort = 0
        letters = "abcdefghijklmnopqrstuvwxyzäöüÄÖÜß".decode("iso-8859-1")
        
        if htmlFile:
            htmlFile.write ("""<html>
<head>
<title>Silbentrennung</title>
<style type="text/css">
  span.ok         { background-color:#e0ffe0; }
  span.unbekannt  { background-color:#fff8f8; color:#ff0000; font-weight:bold; }
  span.mehrdeutig { background-color:#fff8f8; color:#ff4040; }
  span.untrennbar { background-color:#e0ffe0; color:#004000; }
  span.
</style>
</head>
<body>
<h1>Silbentrennung Trennungstest</h1>
<p>
""")
        for w in wordlist:
            if w=="\n":
                if htmlFile: htmlFile.write("</p>\n<p>")
                continue
            # enthält das Wort mindestens zwei verschiedene Buchstaben?
            wlower = w.lower()
            nletters = 0
            for ch in letters:
                if ch in wlower:
                    nletters  += 1
            if nletters >= 2:
                cntWords += 1
                if len(w) < self.minWordLength:
                    cntTooShort += 1
                    if htmlFile:
                        htmlFile.write("<span class='untrennbar' title='untrennbar'>%s</span>\n" % escape(w))
                else:
                    #print w
                    loesung = self.hyphenate(w)
                    if loesung is None:
                        if wlower not in unknownWords:
                            unknownWords.append(wlower)
                    elif loesung.hyphenations:
                        cntOK += 1
                        if htmlFile:
                            x = w
                            ins=0
                            for h in loesung.hyphenations:
                                if h.nl==0 and h.sl==self.shy:
                                    x = x[:ins+h.indx]+h.sl+x[ins+h.indx:]
                                    ins += 1
                            htmlFile.write("<span class=%s title=%s>%s</span>\n" % (quoteattr("ok"), quoteattr(str(loesung.hyphenations)), x))
                        elif VERBOSE:
                            print w, loesung.hyphenations
                    else:
                        if htmlFile:
                            htmlFile.write("<span class=%s title=%s>%s</span>\n" % (quoteattr("nicht trennbar"), quoteattr(hint), escape(w)))
                        elif VERBOSE:
                            print w, "Nicht trennbar:", repr(loesung)
        if htmlFile:
            htmlFile.write("</p></body></html>")
            
        return (cntWords, cntOK, cntTooShort, unknownWords)


    def test(self, encoding="iso-8859-1", outfname="out.html"):
        """
        Testfunktion (Aufruf aus einem Hauptprogramm).
        """
        import sys
        import time
        wortliste = []
        args = sys.argv[1:]

        runs = 1
        out = None
        verbose = False
        while len(args):
            w,args = args[0],args[1:]
            if w=="-v":
                verbose = True
            elif w=="-r":
                runs,args = int(args[0]), args[1:]
            elif w=="-g":
                GENHTML = True
                out = codecs.open(outfname, "wt", encoding)
            elif w=="-f":
                fname,args = args[0],args[1:]
                for zeile in codecs.open(fname,"rt", encoding):
                    spl = zeile.split()
                    wortliste += spl
                    if not spl: wortliste.append("\n")
            else:
                wortliste.append(w.decode(encoding))
        print "%r" % wortliste

        #timer = timeit.Timer(stmt="result=h.learn(wortliste)")
        #timer.timeit(runs)
        startzeit = time.clock()
        for x in range(runs):
            print "run %d" % x
            result = self.learn(wortliste, VERBOSE=verbose, htmlFile=out)
        endezeit = time.clock()
        cntWords,cntOK,cntTooShort,unknownWords = result

        print """

    Statistics:
    -----------
    Words processed   :%6d
    Bytes processed   :%6d
    Short words       :%6d
    Unknown words     :%6d
    """ % (cntWords, sum(map(len,wortliste)), cntTooShort, len(unknownWords))

        secs = endezeit-startzeit
        print "%d runs" % runs
        print "Time   :%3.3f seconds" % secs
        if cntWords:
            print " = %1.6f secs per 1000 words and run" % (1000* secs / (runs * cntWords))

        unknownWords.sort()
        print "unknown words (sorted):"
        w_ = None
        for w in unknownWords:
            if w!=w_:
                if len(w)>6: print "%-15.15s" % w,
                w_ = w


    def testWordList(self, fname, encoding, error):
        """
        Test a file containing a list of word and hyphenated word in the form
        someword  some-word
        E.g. each line is a test case.
        The test outputs those words where the hyphenated version does not match
        the expected output.
        """
        for zeile in codecs.open(fname,"rt", encoding):
            assert isinstance(zeile,unicode)
            word, expected = zeile.strip().split()
            loesung = self.hyphenate(word)
            if loesung.hyphenations:
                x = word
                ins=0
                for h in loesung.hyphenations:
                    h.sl = h.sl.replace(SHY, "-")
                    ###if h.nl==0 and h.sl==self.shy:
                    x = x[:ins+h.indx]+h.sl+x[ins+h.indx:]
                    ins += len(h.sl) - h.nl
                output = x
            else:
                output = word
            if output != expected:
                error ("%r: output=%r but expected=%r", word, output, expected)
            
        
if __name__=="__main__":
    print "Testing BaseHyphenator:"
    h = BaseHyphenator("DE",5)
    if len(sys.argv) > 1:
        h.test(outfname="ExplicitLearn.html")
        sys.exit()
    #assert h.hyphenate("Exklusiv-Demo") == [(9,9,None)]
    for word in ["Exklusiv-Demo", "18.10.2003", "1,2345", "i.e", "z.B.", "-0.1234", "reportlab-users", "no_data_found", "-12345", "12345-", "1-2345", "1234-5"]:
        hyphWord = h.hyphenate(word.decode("iso-8859-1"))
        print "%s -- %s" % (word, hyphWord.showHyphens())
    
    hw = HyphenatedWord("Schiffahrtskapitänsbackenzahn".decode("iso-8859-1"))
    #                   0         1         2
    #                   01234567890123456789012345678
    hw.hyphenations = [HyphenationPoint(5,8,0,u"f"+SHY,0,u""), #schif(f)-fahrt
                       #HyphenationPoint(6,8,0,SHY,0,u"f"), # eine Alternative Darstellung mit gleichem Ergebnis
                       HyphenationPoint(11,9,0,SHY,0,u""), #fahrts-ka
                       HyphenationPoint(13,4,0,SHY,0,u""), #ka-pi
                       HyphenationPoint(15,4,0,SHY,0,u""), #pi-täns
                       HyphenationPoint(19,9,0,SHY,0,u""), #täns-ba
                       HyphenationPoint(22,4,1,u"k"+SHY,0,""), # bak-ken nach alten Regeln
                       HyphenationPoint(25,9,0,SHY,0,u""), # ken-zahn
                      ]
    print "%s -- %s" % (hw.word,hw.showHyphens())
    while len(hw.hyphenations):
        l,r = hw.split(hw.hyphenations[0])
        print "%s%s" % (l,r.word)
        hw=r
