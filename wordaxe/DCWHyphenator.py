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

import os,sys
import sets
import copy
import operator
import codecs

from wordaxe.hyphen import SHY,HyphenationPoint,HyphenatedWord
import time
from wordaxe.BaseHyphenator import Stripper, BaseHyphenator
from wordaxe.ExplicitHyphenator import ExplicitHyphenator

from wordaxe.hyphrules import HyphRule, RULES, AlgorithmError

from wordaxe.hyphrules import NO_CHECKS,StringWithProps,Prefix,Root,Suffix
from wordaxe.hyphrules import TRENNUNG,NO_SUFFIX,KEEP_TOGETHER

DEBUG=0

import logging
logging.basicConfig()
log = logging.getLogger("DCW")
log.setLevel(logging.INFO)
if DEBUG:
    log.setLevel(logging.DEBUG)

class WordFrag:
    """Helper class for a (partially) parsed WordFrag.
       A WordFrag is made up from prefixChars, prefix, root, suffix, and suffixChars,
       i.e. the german word "(unver�nderbarkeit)!" 
       is a WordFrag ( "(", ["un","ver"], "�nder", ["bar","keit"], ")!" ).
    """
       
    def __init__(self,konsonantenverkuerzung_3_2=False):
        self.konsonantenverkuerzung_3_2 = konsonantenverkuerzung_3_2
        self.prefixChars = ""
        self.prefix = []
        self.root = None
        self.suffix = None
        self.suffixChars = ""
        self.checks = [[],[],[],[],[],[]]

    def isValid(self):
       "Is the WordFrag (stand alone) a valid word?"
       return False
       
    def __str__(self):
       "String representation"
       return self.__class__.__name__
       
    def __repr__(self):
       return self.__str__()
    
    def clone(self):
        return copy.copy(self)

class PrefixWordFrag(WordFrag):
    """A WordFrag that does not yet contain the root.
    """
    def __init__(self,tw,prefixChars="",prefix=[]):
        if tw is None: tw = WordFrag()
        # Auch alle sonstigen Attribute der Vorlage mit �bernehmen
        # @TODO Dieser Code ist wirklich h�sslich:
        self.__dict__.update(tw.__dict__)
        WordFrag.__init__(self,konsonantenverkuerzung_3_2=tw.konsonantenverkuerzung_3_2)
        self.prefixChars = prefixChars or tw.prefixChars
        self.prefix = prefix or tw.prefix

    def __str__(self):
       "String representation"
       return "PrefixWF " + self.prefixChars + "-".join([p.strval for p in self.prefix])

    def clone(self):
        n = copy.copy(self)
        n.prefix = self.prefix[:]
        return n
        
class SuffixWordFrag(PrefixWordFrag):
    """A WordFrag that does contain a root and eventually a suffix.
    """
    def __init__(self,tw,root=None,suffix=[],suffixChars=[]):
        if tw is None: tw = PrefixWordFrag(None,[])
        PrefixWordFrag.__init__(self,tw)
        self.root = root or tw.root
        self.suffix = suffix
        self.suffixChars = suffixChars

    def __str__(self):
       "String representation"
       return "SuffixWF " + self.prefixChars + "-".join([p.strval for p in self.prefix]) + \
              "|" + self.root.strval + "|" + ":".join([s.strval for s in self.suffix]) + \
              (self.konsonantenverkuerzung_3_2 and "!3>2" or "")

    def clone(self):
        n = copy.copy(self)
        n.suffix = self.suffix[:]
        
        return n

    def isValid(self):    
        if not self.suffix:
            for p in self.root.props:
                if isinstance (p,NEED_SUFFIX):
                    return False
        return True
        
SWORD = SuffixWordFrag

VOWELS = "aeiou���y".decode("iso-8859-1")

ALTE_REGELN = False

KONSTANTEN_VERKUERZUNG_3_2 = True

VERBOSE = False

GENHTML = False

class DCWHyphenator(ExplicitHyphenator):
    """
    Hyphenation by decomposition of composed words.
    The German language has a lot of long words that are
    composed of simple words. The German word
    "Silbentrennung" (engl. hyphenation) is a good example
    in itself.
    It is a composition of the words "Silbe" (engl. syllable)
    and "Trennung" (engl. "separation").
    Each simple word consists of 0 or more prefixes, 1 stem,
    and 0 or more suffixes.
    The principle of the algorithm is quite simple.
    It uses a a base of known prefixes, stems and suffixes,
    each of which may contain attributes that work as rules.
    The rules define how these word fragments can be combined.
    The algorithm then to decompose the whole word into a
    series of simple words, where each simple word consists
    of known fragments and fulfills the rules.
    Then it uses another simple algorithm to hyphenate each
    simple word.
    For a given word, there may be more than one possible
    decomposition into simple words.
    The hyphenator only returns those hyphenation points that
    ALL possible decompositions have in common.
    
    Note:
    The algorithm has been inspired by the publications about
    "Sichere sinnentsprechende Silbentrennung" from the 
    technical university of Vienna, Austria (TU Wien).
    However, it is in no other way related to the closed-source
    software "SiSiSi" software developed at the TU Wien.
    For more information about the "SiSiSi" software, see the
    web site "http://www.ads.tuwien.ac.at/research/SiSiSi/".
    """

    def __init__ (self, 
                  language="DE",
                  minWordLength=4,
                  qHaupt=8,
                  qNeben=5,
                  qVorsilbe=5,
                  qSchlecht=3,
                  hyphenDir=None
                 ):
        ExplicitHyphenator.__init__(self,language=language,minWordLength=minWordLength)

        # Qualit�ten f�r verschiedene Trennstellen
        self.qHaupt=qHaupt
        self.qNeben=qNeben
        self.qVorsilbe=qVorsilbe
        self.qSchlecht=qSchlecht
        
        # Stammdaten initialisieren
        special_words = []
        self.stamm = []
        self.prefixes = []
        self.suffixes = []
        self.prefixChars = []
        self.suffixChars = []
        self.maxLevel=20
        
        # Statistikdaten initialisieren
        self.numStatesExamined = 0
        
        # Datei einlesen
        if hyphenDir is None:
            hyphenDir = os.path.join (os.path.split(__file__)[0], "dict")
        wortDateiName = os.path.join(hyphenDir, "%s_hyph.ini"%language)
        wortdatei = open(wortDateiName, "rt")
        abchnitt = None
        propsCanFollow = True
        cls = None
        encoding = None
        for z in wortdatei:
            zeile = z.strip()
            if zeile.startswith("# -*- coding: "):
                encoding = zeile[14:].replace("-*-", "")
            elif zeile and zeile[0] != "#":
                zeile = zeile.decode(encoding)
                assert isinstance(zeile,unicode)
                if zeile[0]=="[" and zeile[-1:]=="]":
                    log.debug("Abschnitt: %s", zeile)
                    if zeile=="[roots]":
                        abschnitt = self.stamm
                        propsCanFollow = True
                        cls = Root
                    elif zeile=="[special_words]":
                        abschnitt = special_words
                        propsCanFollow = True
                        cls = StringWithProps
                    elif zeile=="[prefixes]":
                        abschnitt = self.prefixes
                        propsCanFollow = True
                        cls = Prefix
                    elif zeile=="[suffixes]":
                        abschnitt = self.suffixes
                        propsCanFollow = True
                        cls = Suffix
                    elif zeile=="[prefix-chars]":
                        abschnitt = self.prefixChars
                        propsCanFollow = False
                        cls = str
                    elif zeile=="[postfix-chars]":
                        abschnitt = self.suffixChars
                        propsCanFollow = False
                        cls = str
                else:

                    # Sonderbehandlung [special_words]
                    if abschnitt is special_words:
                        if "=" in zeile:
                            word, trennung = zeile.split("=")
                        else:
                            zeile = zeile.split(",")
                            word = zeile.pop(0)
                            assert len(zeile) >= 1
                            for attr in zeile:
                                if ":" in attr:
                                    propnam, propval = attr.split(":")
                                else:
                                    propnam, propval = attr, ""
                                if propnam == u"TRENNUNG":
                                    trennung = propval
                                elif propnam == u"KEEP_TOGETHER":
                                    trennung = word
                                else:
                                    raise NameError("Unknown property for word %s: %s" % (word, propnam))
                                    pass # Attribut ignorieren
                        self.add_entry(word, trennung)
                        
                    elif propsCanFollow:
                        zeile = zeile.split(",")
                        word = zeile.pop(0)
                        props = []
                        if len(zeile) >= 1:
                          for attr in zeile:
                            if ":" in attr:
                                [propnam,propval] = attr.split(":")
                            else:
                                propnam = attr
                                propval = ""
                            try:
                                cls = RULES[propnam]
                                props.append(cls(propval)) # the class is the propnam
                            except KeyError:
                                raise NameError("Unknown property for word %s: %s" % (word,propnam))

                        lenword = len(word)
                        for (lae,L) in abschnitt:
                            if lae==lenword:
                              try:
                                  L[word].append(props)
                              except KeyError:
                                  L[word]=[props]
                              break
                        else:
                            abschnitt.append((lenword,{word:[props]}))
                    else:
                        abschnitt.append(zeile)
        assert len(self.prefixChars) <= 1
        self.prefixChars = self.prefixChars[0]
        assert len(self.suffixChars) <= 1
        self.suffixChars = self.suffixChars[0]
        wortdatei.close()
        self.stripper = Stripper(self.prefixChars, self.suffixChars)

    def _zerlegeWort(self,zusgWort):
        """"
        Returns a list containing all possible decompositions.
        The decomposition routine works as follows:

        A TODO list contains the cases that still have to be considered.
        Each element in this list is a tuple
        (cword,frag,remainder,checks) characterising the state precisely.
        
        Notation:
        CWORD = compound word, a list of SWORDs
        SWORD = simple word = prefix* root suffix*

        cword is a list containing the already parsed SWORDs.
        frag is a fragment of the current SWORD.
        remainder is the remainder of the unparsed words.
        checks describes the checks we still have to do.
        
        A solution list contains the solutions found so far
        (it is empty in the beginning).
        
        In the beginning, the TODO-list contains only one element,
        the initial status:
        ([], None, zusgWort, [])
        
        For the word "Wegbeschreibung", a status could
        look like this:
        ( [ SWORD([],Root("Weg"),[]) ],
          SuffixWordFrag ([Prefix("be")],Root("schreib"),[]),
          "ung",
          []
        )
        
        If the TODO list is empty, the solutions found are returned.
        
        Otherwise, one element of the list is removed and examined.
        Depending on the frag, we try all possible extensions of the
        frag with a prefix,root or postfix.
        If a continuation is possible, then the continued frag
        and is appended to the TODO list.
        """

        def mergeChecks(c1,c2):
            """Create a new list of checks from c1 and c2
            """
            return map(operator.__add__,c1,c2)
        
        def do_check_frag(when,cword,frag,checks):
            """Run the PRE_WORD or PRE_NEXT_WORD checks before appending frag to cword.
            """
            for chk in checks[when]:
              try:
                if not chk.check(cword,when,frag):
                    #log.debug ("check (chk=%r, when=%d) failed for frag %r", chk, when, frag)
                    return False
              except AlgorithmError:
                log.error ("check %s when=%d : AlgorithmError for cword=%r, frag=%r", chk, when, cword, frag)
                return False
            return True
        
        def do_check_piece(when,frag,piece,checks):
            """Run the PRE_PIECE or PRE_NEXT_PIECE checks before appending piece to frag.
            """
            for chk in checks[when]:
                if not chk.check(frag,when,piece):
                    log.debug ("check (chk=%r, when=%d) failed for piece %r", chk, when, piece.strval)
                    return False
            return True
        
        def check_PRE_WORD(cword,frag,checks):
            return do_check_frag(HyphRule.PRE_WORD,cword,frag,checks)

        def check_PRE_NEXT_WORD(cword,frag,checks):
            return do_check_frag(HyphRule.PRE_NEXT_WORD,cword,frag,checks)

        def check_AT_END(cword,checks):
            return do_check_frag(HyphRule.AT_END,cword,None,checks)
        
        def check_PRE_PIECE(frag,piece,checks):
            return do_check_piece(HyphRule.PRE_PIECE,frag,piece,checks)

        def check_PRE_NEXT_PIECE(frag,piece,checks):
            return do_check_piece(HyphRule.PRE_NEXT_PIECE,frag,piece,checks)

        def check_PRE_ROOT(frag,piece,checks):
            return do_check_piece(HyphRule.PRE_ROOT,frag,piece,checks)

        # Initialization
        solutions = []
        todo = []
        state = ( [], None, zusgWort, NO_CHECKS())
        todo.append (state)
        
        while todo:

            #log.debug ("todo=\n%r", todo)
            
            # Consider the next state
            state = todo.pop()
            (cword,frag,remainder,checks) = state
            
            log.debug ("Examining state: %r", state)
            self.numStatesExamined += 1
            
            # check if the SWORD can end here
            if frag and frag.root \
            and check_PRE_WORD(cword,frag,checks) \
            and check_PRE_NEXT_WORD(cword,frag,checks):
                #### log.warn ("@TODO: The above IF statement is DEFINITELY wrong - frag: %r", frag)
                #### Ich bin mir da nicht mehr so sicher, es scheint doch richtig zu sein.

                #log.debug ("Since fragment has a root, add test with None.")
                newChecks = NO_CHECKS()
                newChecks[HyphRule.AT_END] = checks[HyphRule.AT_END]
                todo.append( (cword+[frag],None,remainder,newChecks) )
            
            if remainder=="":  # we have reached the end of the word.

                if frag is None:  # good, we have no incomplete fragment
                
                    if check_AT_END(cword,checks): # the last checks are ok
                        log.debug ("found solution: %r", cword)
                        solutions.append(cword)
                    else:
                        pass
                        log.debug ("check_AT_END failed for %r", cword)
                        
                else: # we have a fragment of an SWORD.
                    pass
                    #log.debug ("Incomplete or invalid sword fragment found at end of string.\n" +
                    #    "We should already have added the case where fragment is None\n" +
                    #    "to our todo list, so we just can skip this case: %r", frag)

                        
            else:  # still more characters to parse
            
                if frag is None: 
                
                    log.debug ("frag is None, remainder=%r bei zerlegeWort %r", remainder, zusgWort)
                
                    # check prefix characters
                    l = 0
                    while l<len(remainder) and remainder[l] in self.prefixChars:
                        l = l+1
                    if l>0:
                        ###HVB, 14.10.2006 ge�ndert
                        ###newfrag = frag.clone()
                        ###newfrag.prefixChars = remainder[:l]
                        ###r = remainder[l:]
                        ###todo.append ( (cword,newfrag,r,checks) )
                        ###continue # do not examine the current state any more.
                        newfrag = PrefixWordFrag(None, prefixChars=remainder[:l])
                        r = remainder[l:]
                        todo.append ( (cword,newfrag,r,checks) )
                        continue # do not examine the current state any more.
                    else:
                        # we need a fragment (even if it is empty) from here on.
                        frag = PrefixWordFrag(None)
                
                if not frag.root: # fragment has not yet a root.

                    # check all possible prefixes.
                    #log.debug ("checking prefixes.")
                    for (lae,L) in self.prefixes:
                      l,r = remainder[:lae],remainder[lae:]
                      for eigenschaften in L.get(l,[]):
                          #log.debug ("trying prefix: %s with properties: %s", l,eigenschaften)
                          piece = Prefix(l,eigenschaften)
                          pChecks = piece.getChecks()
                          if check_PRE_PIECE(frag,piece,pChecks):
                              if check_PRE_NEXT_PIECE(frag,piece,checks):
                                  # @TODO perhaps the next few lines could be faster and more elegant
                                  newChecks = mergeChecks(checks,pChecks)
                                  newChecks[HyphRule.PRE_PIECE] = []
                                  newChecks[HyphRule.PRE_NEXT_PIECE] = pChecks[HyphRule.PRE_NEXT_PIECE]
                                  newfrag = copy.copy(frag)
                                  newfrag.prefix = frag.prefix + [piece]
                                  todo.append( (cword,newfrag,r,newChecks) )
                              else:
                                  pass # pre next piece checks failed
                          else:
                              pass # pre piece checks failed
                     
                    # check all possible roots.
                    #log.debug ("checking roots.")
                    for (lae,L) in self.stamm:
                      l,r = remainder[:lae],remainder[lae:]
                      for eigenschaften in L.get(l,[]):
                          #log.debug ("trying root: %r with properties: %r", l,eigenschaften)
                          piece = Root(l,eigenschaften)
                          if check_PRE_ROOT(frag,piece,checks):
                              pChecks = piece.getChecks()
                              if check_PRE_PIECE(frag,piece,pChecks):
                                  if check_PRE_NEXT_PIECE(frag,piece,checks):
                                      # @TODO perhaps the next few lines could be faster and more elegant
                                      newChecks = mergeChecks(checks,pChecks)
                                      newChecks[HyphRule.PRE_PIECE] = []
                                      newChecks[HyphRule.PRE_NEXT_PIECE] = pChecks[HyphRule.PRE_NEXT_PIECE]
                                      newfrag = SuffixWordFrag(frag,piece)
                                      todo.append( (cword,newfrag,r,newChecks) )
                                      # Auch Verk�rzung von 3 Konsonanten zu zweien ber�cksichtigen
                                      if KONSTANTEN_VERKUERZUNG_3_2 and l[-1]==l[-2] and l[-1] not in VOWELS:
                                          #log.debug ("konsonantenverkuerzung %s",l)
                                          newChecks = mergeChecks(checks,pChecks)
                                          newChecks[HyphRule.PRE_PIECE] = []
                                          # Konsonsantenverk�rzung kommt nur bei Haupttrennstellen
                                          # vor, nicht vor Suffixes.
                                          newChecks[HyphRule.PRE_NEXT_PIECE] = [NO_SUFFIX()] + pChecks[HyphRule.PRE_NEXT_PIECE]
                                          newPiece = Root(l,eigenschaften)
                                          newfrag = SuffixWordFrag(frag,newPiece)
                                          newfrag.konsonantenverkuerzung_3_2 = True
                                          todo.append( (cword,newfrag,l[-1]+r,newChecks) )
                                  else:
                                      pass # pre next piece checks failed
                              else:
                                  pass # pre piece checks failed
                          else: # pre root checks failed
                              pass

                else: # fragment already has a root.
                    #log.debug ("checking suffixes.")
                    # check all possible suffixes.
                    for (lae,L) in self.suffixes:
                      l,r = remainder[:lae],remainder[lae:]
                      for eigenschaften in L.get(l,[]):
                          log.debug ("trying suffix: %r with properties: %s", l,eigenschaften)
                          piece = Suffix(l,eigenschaften)
                          pChecks = piece.getChecks()
                          if check_PRE_PIECE(frag,piece,pChecks):
                              if check_PRE_NEXT_PIECE(frag,piece,checks):
                                  # @TODO perhaps the next few lines could be faster and more elegant
                                  newChecks = mergeChecks(checks,pChecks)
                                  newChecks[HyphRule.PRE_PIECE] = []
                                  newChecks[HyphRule.PRE_NEXT_PIECE] = pChecks[HyphRule.PRE_NEXT_PIECE]
                                  newfrag = copy.copy(frag)
                                  newfrag.suffix = frag.suffix + [piece]
                                  todo.append( (cword,newfrag,r,newChecks) )
                                  
                              else:
                                  log.debug("pre next piece checks failed")
                                  pass # pre next piece checks failed
                          else:
                              log.debug("pre piece checks failed")
                              pass # pre piece checks failed
                     
                    # check suffix characters
                    if not frag.suffixChars:
                        l = 0
                        while l<len(remainder) and remainder[l] in self.suffixChars:
                            l = l+1
                        if l>0:
                            newfrag = frag.clone()
                            newfrag.suffixChars = remainder[:l]
                            r = remainder[l:]
                            if check_PRE_WORD(cword,frag,checks) \
                            and check_PRE_NEXT_WORD(cword,frag,checks):
                                #log.debug ("@TODO: The above IF statement is definitely wrong.\n" + 
                                #    "We have to distinguish between the checks for CWORD and FRAG.\n" +
                                #    "Thus it seems that we need TWO check variables.")
                                chks = NO_CHECKS(HyphRule.AT_END) + checks[HyphRule.AT_END:]
                                todo.append ( (cword+[newfrag],None,r,chks) )
                                continue # do not examine the current state any more.
                            else: # checks failed
                                pass
                        else: # no suffix characters found
                            pass
                    else:
                        pass # we already have suffix characters.
            
        # Nothing more to do.
        if VERBOSE: log.info ("returning %r", solutions)
        return solutions

    # Hilfsfunktion
    def schiebe(self,offset,L):
        return [HyphenationPoint(h.indx+offset,h.quality,h.nl,h.sl,h.nr,h.sr) for h in L]

    def dudentrennung(self,wort,quality=None):
        """ 
            The algorithm how to hyphenate a word
            without knowing about the context.

            This code is quite specific to German!
            For other languages, there may be totally different rules.
            
            This rule is known as "Ein-Konsonanten-Regel" in German.
            The rule works (basically) as follows:
            First, find the vowels in the word,
            as they mark the syllables (one hyphenation point between
            two vowels (but consider sequences of vowels counting as one).
            If there are consonants between two vowels,
            put all but the last consonant to the left syllable,
            and only the last consonant to the right syllable
            (therefore the name one-consonant-rule).
            However, there are also sequences of consonants counting as one,
            like "ch" or "sch".
        """
        #print "dudentrennung: %s" % wort
        if not quality: quality = self.qNeben
        
        assert isinstance(wort, unicode)

        # Jede Silbe muss mindestens einen Vokal enthalten
        if len(wort) <= 2:
            return []
        # Suche bis zum ersten Vokal
        for vpos1 in range(len(wort)):
            if wort[vpos1] in VOWELS:
              if wort[vpos1-1:vpos1+1] != 'qu':
                break
        else:
            # Kein Vokal enthalten!
            return []
        # wort[vpos1] ist der erste Vokal
        fertig = False
        stpos = vpos1+1
        while not fertig:
            fertig = True
            # Suche bis zum zweiten Vokal
            for vpos2 in range(stpos,len(wort)):
                if wort[vpos2] in VOWELS:
                    break
            else:
                # Kein zweiter Vokal enthalten!
                return []
            # wort[vpos2] ist der zweite Vokal
            if vpos2==2 and wort[1] not in VOWELS:
                # Nach Einkonsonantenregel bleibt als erste Silbe nur ein einzelner Buchstabe,
                # z.B. o-ber. Das wollen wir nicht
                stpos = vpos2+1
                fertig = False
            if vpos2==vpos1+1:
                # a sequence of two vowels, like German "ei" or "au", or English "ou" or "oi"
                if wort[vpos1:vpos2+1] in [u'�u', u'au', u'eu', u'ei', u'ie', u'ee']:
                    # Treat the sequence as if it was one vowel!
                    stpos = vpos2+1
                    fertig = False
                else:
                    return [HyphenationPoint(vpos2,quality,0,self.shy,0,u"")] + self.schiebe(vpos2,self.dudentrennung(wort[vpos2:],quality))
        if wort[vpos2-3:vpos2] in [u'sch',]:
            return [HyphenationPoint(vpos2-3,quality,0,self.shy,0,u"")]     + self.schiebe(vpos2-3,self.dudentrennung(wort[vpos2-3:],quality))
        elif ALTE_REGELN and wort[vpos2-2:vpos2] in [u'st']:
            return [HyphenationPoint(vpos2-2,quality,0,self.shy,0,u"")]     + self.schiebe(vpos2-2,self.dudentrennung(wort[vpos2-2:],quality))
        elif ALTE_REGELN and wort[vpos2-2:vpos2] in [u'ck']:
            return [HyphenationPoint(vpos2-1,quality,1,u"k"+self.shy,0,u"")] + self.schiebe(vpos2-1,self.dudentrennung(wort[vpos2-1:],quality))
        elif wort[vpos2-2:vpos2] in [u'ch',u'ck', u'ph']:
            return [HyphenationPoint(vpos2-2,quality,0,self.shy,0,u"")]     + self.schiebe(vpos2-2,self.dudentrennung(wort[vpos2-2:],quality))
        elif wort[vpos2-1] in VOWELS:
            return [HyphenationPoint(vpos2  ,quality,0,self.shy,0,u"")]     + self.schiebe(vpos2,  self.dudentrennung(wort[vpos2:],quality))
        else:
            return [HyphenationPoint(vpos2-1,quality,0,self.shy,0,u"")]     + self.schiebe(vpos2-1,self.dudentrennung(wort[vpos2-1:],quality))

    def zerlegeWort(self,zusgWort,maxLevel=20):

        #Wort erstmal normalisieren
        assert isinstance(zusgWort,unicode)
        zusgWort = zusgWort.lower().replace(u'�',u'�').replace(u'�',u'�').replace(u'�',u'�')
        lenword = len(zusgWort)
        #print zusgWort
        loesungen = []

        L = self._zerlegeWort(zusgWort)
        # Trennung f�r Wortst�mme mit Endungen berichtigen
        for W in L:
            # Eine m�gliche L�sung. Von dieser die einzelnen W�rter betrachten
            Wneu = []
            offset = 0
            ok = True
            #log.debug ("Versuche %r", W)
            sr = ""
            for i,w in enumerate(W):
                if not ok: break
                offset += len(w.prefixChars)
                if i>0:
                    # @TODO: Hier darf nicht fest shy stehen, da
                    # das letzte Wort mit "-" geendet haben k�nnte
                    lastWordSuffixChars = W[i-1].suffixChars
                    if lastWordSuffixChars and lastWordSuffixChars[len(lastWordSuffixChars)-1][-1:] in [u"-",self.shy]:
                        Wneu.append(HyphenationPoint(offset,self.qHaupt,0,"",0,sr))
                    else:
                        Wneu.append(HyphenationPoint(offset,self.qHaupt,0,self.shy,0,sr))
                if w.konsonantenverkuerzung_3_2:
                    sr = w.root.strval[-1]
                else:
                    sr = u""

                if w.prefix:
                    for f in w.prefix:
                        Wneu += self.schiebe(offset,self.dudentrennung(f.strval,self.qVorsilbe))
                        offset += len(f.strval)
                        Wneu.append(HyphenationPoint(offset,7,0,self.shy,0,u""))
                        # @TODO Qualit�t 7 ist hier fest eingebrannt
                for p in w.root.props:
                  if isinstance(p,TRENNUNG) or isinstance(p,KEEP_TOGETHER):
                    st = p.args
                    break
                else:
                    st = self.dudentrennung(w.root.strval,self.qSchlecht)
                if len(st):
                    Wneu += self.schiebe(offset,st)
                    st,stLast = st[:-1],st[-1]
                    p = stLast.indx
                    offset += p
                    en = w.root.strval[p:]+(u"".join([s.strval for s in w.suffix]))
                else:
                    en = w.root.strval+(u"".join([s.strval for s in w.suffix]))
                if w.suffix:
                    ent = self.dudentrennung(en,self.qNeben)
                    #print "en=",en,"ent=",ent
                    Wneu += self.schiebe(offset,ent)
                    # Pr�fen, ob dieses Wort als letztes stehen muss
                #
                #for pf in w.prefix + [w.root] + w.suffix:
                #    if i>0 and pf.props.get(NOT_AFTER_WORD) and str(W[i-1].root) in pf.props.get(NOT_AFTER_WORD):
                #        if VERBOSE: print "'%s' nicht erlaubt nach '%s'" % (pf,W[i-1].root)
                #        ok = False
                #        break
                #    if pf.props.get(ONLY_LAST_WORD) and i<len(W)-1:
                #        if VERBOSE: print "'%s' nur als letztes Wort erlaubt!" % pf
                #        ok = False
                #        break
                #    if pf.props.get(ONLY_FIRST_WORD) and i>0:
                #        if VERBOSE: print "'%s' nur als erstes Wort erlaubt!" % pf
                #        ok = False
                #        break
                #else: 
                #  # letztes Wort
                #  for pf in w.prefix + [w.root] + w.suffix:
                #    #print "letztes Wort, Bestandteil",pf, pf.props
                #    if pf.props.get(NOT_LAST_WORD):
                #        if VERBOSE: print "'%s' nicht als letztes Wort erlaubt!" % pf
                #        ok = False
                #        break
                offset += len(en)
                offset += len(w.suffixChars)
            if ok and (Wneu not in loesungen):
                log.debug ("Wneu=%r", Wneu)
                loesungen.append(Wneu)

        return loesungen
        
    def hyph(self,word):
        log.debug ("hyphenate %r", word)
        assert isinstance(word, unicode)
        loesungen = self.zerlegeWort(word)
        if len(loesungen) > 1:
            # Trennung ist nicht eindeutig, z.B. bei WachsTube oder WachStube.
            #hword.info = ("AMBIGUOUS", loesungen)
            # nimm nur solche Trennstellen, die in allen L�sungen vorkommen,
            # und f�r die Qualit�t nimm die schlechteste.
            loesung = []
            loesung0, andere = loesungen[0], loesungen[1:]
            for i,hp in enumerate(loesung0):
                q = hp.quality
                for a in andere:
                    if q:
                        for hp1 in a:
                            if hp1.indx==hp.indx \
                            and hp1.nl==hp.nl and hp1.sl==hp.sl \
                            and hp1.nr==hp.nr and hp1.sr==hp.sr:
                                q = min(q,hp1.quality)
                                break
                        else:
                            # Trennstelle nicht in der anderen L�sung enthalten
                            q = 0
                if q:
                    loesung.append(HyphenationPoint(hp.indx,q,hp.nl,hp.sl,hp.nr,hp.sr))
            if loesung:
                # Es gibt mindestens eine Trennstelle, die bei allen Varianten
                # enthalten ist, z.b. Wachstu-be.
                pass 
                # hword.info = ("HYPHEN_OK", loesung)
            else:
                # Es gibt keine Trennstelle.
                pass
        elif len(loesungen) == 1:
            # Trennung ist eindeutig
            loesung = loesungen[0]
            #hword.info = ("HYPHEN_OK", loesung)
            if not loesung:
                pass # hword.info = ("NOT_HYPHENATABLE", aWord)
        else:
            # Das Wort ist uns unbekannt.
            return None
        return HyphenatedWord(word, loesung)
        
    def i_hyphenate(self,aWord):
        assert isinstance(aWord, unicode)
        # Zun�chst einmal ganz grob trennen (nur bei "-").
        #words = aWord.split(u"-")
        #hwords = []
        #for indx, word in enumerate(words):
        #    if not word:
        #        # Nur "-"
        #        raise NotImplementedError("Sonderfall -", aWord, words)
        #    if indx + 1 < len(words):
        #        words[indx] = words[indx] + u"-"
        hwords = []
        rest = aWord
        words = []
        while rest:
            i = rest.find(u"-")
            if i<0 or i+1==len(rest):
                words.append(rest)
                break
            words.append(rest[:i+1])
            rest = rest[i+1:]
        assert words, "words is leer bei Eingabe %r" % aWord
        for indx, word in enumerate(words):
            if not word:
                # Nur "-"
                raise NotImplementedError("Sonderfall -", aWord, words)
            if SHY in word:
                # Das Wort ist vorgetrennt
                hword = BaseHyphenator.hyph(self,word)
            else:
                # Pr�fen, ob Trennung explizit vorgegeben (Sonderf�lle)
                def func(word):
                    return ExplicitHyphenator.hyph(self, word)
                hword = self.stripper.apply_stripped(word, func)
                if hword is None:
                    hword = self.stripper.apply_stripped(word, self.hyph)
            hwords.append(hword)
        assert len(hwords) == len(words)
        if len(words) > 1:
            assert u"".join(words) == aWord, "%r != %r" % (u"".join(words), aWord)
            for indx in range(len(words)):
                if hwords[indx] is None:
                    hwords[indx] = HyphenatedWord(words[indx])
            return HyphenatedWord.join(hwords)
        else:        
            return hwords[0] # Kann auch None sein.

if __name__=="__main__":
    h = DCWHyphenator("DE",5)
    h.test(outfname="DCWLearn.html")
