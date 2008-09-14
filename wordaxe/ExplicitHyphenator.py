#!/bin/env/python
# -*- coding: iso-8859-1 -*-

__license__="""
   Copyright 2004-2008 Henning von Bargen (henning.vonbargen arcor.de)
   This software is dual-licenced under the Apache 2.0 and the
   2-clauses BSD license. For details, see license.txt
"""

__version__=''' $Id: __init__.py,v 1.2 2004/05/31 22:22:12 hvbargen Exp $ '''

from wordaxe.hyphen import SHY, HyphenatedWord
from wordaxe.BaseHyphenator import BaseHyphenator
from wordaxe.hyphrules import decodeTrennung

class ExplicitHyphenator(BaseHyphenator):
    """
    Allow to explicitly specify how a word should be hyphenated.
    This is a slight improvement compared to BaseHyphenator.
    
    Usage:
    
    hyphenator = ExplicitHyphenator("DE")
    # Add explicit hyphenation for a single word.
    hyphenator.add_entry(u"analphabet", u"an8alpha5bet")
    # Add several entries
    hyphenator.add_entries({u"urinstinkt":   u"ur8instinkt",
                            u"urinstinkte":  u"ur8instinkte",
                            u"urinstinkten": u"ur8instinkt3en",
                           })
    
    The last entry is probably not correctly hyphenated
    according to the german hyphenation rules, but you don't
    want to read "urinstink" in a text...
    
    The add_entry/add_entries usually expect unicode strings.
    Bytes strings require the encoding argument to be supplied.
    hyphenator.add-entries ("bräutigam", "bräu5ti5gam", encoding="iso-8859").
    
    Instead of using numbers for defining the quality of a hyphenation
    point, you may use the "~" (tilde) character, corresponding to
    a medium quality hyphenation point: "bräu~ti~gam".
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
        BaseHyphenator.__init__(self,language=language,minWordLength=minWordLength)

        # Qualitäten für verschiedene Trennstellen
        self.qHaupt=qHaupt
        self.qNeben=qNeben
        self.qVorsilbe=qVorsilbe
        self.qSchlecht=qSchlecht
        
        # Stammdaten initialisieren
        self.sonderfaelle = []
        
    def add_entry(self, word, trennung, encoding=unicode):
        if not isinstance(word, unicode):
            word = unicode(word, encoding)
        if not isinstance(trennung, unicode):
            trennung = unicode(trennung, encoding)
        # Ignore Case @TODO Umlaute usw.!
        word = word.lower() 
        trennung = trennung.replace(u"~", u"5")
        lenword = len(word)
        for (lae, L) in self.sonderfaelle:
            if lae == lenword:
                L[word] = trennung
                break
        else:
            self.sonderfaelle.append((lenword,{word: trennung}))
            
    def add_entries(self, mapping, encoding=unicode):
        for word, trennung in mapping.items():
            self.add_entry(word, trennung)
        
    def hyph(self, word):
        hword = BaseHyphenator.hyph(self, word)
        if hword is not None:
            return hword
        lenword = len(word)
        for (lae, L) in self.sonderfaelle:
            if lae == lenword:
                trennung = L.get(word.lower(), None)
                if trennung is not None:
                    hword = HyphenatedWord(word, decodeTrennung(trennung))
                    return hword
                break
        # Wort nicht gefunden
        return None
        
    def i_hyphenate(self, aWord):
        assert isinstance(aWord, unicode)
        return self.stripper.apply_stripped(aWord, self.hyph)

    def i_hyphenate_derived(self,aWord):
        """
        You can use this method in classes derived from ExplicitHyphenator.
        It will first split the word using BaseHyphenator,
        then for each "subword" it will call ExplicitHyphenator,
        and only call the derived classes hyph method for the still
        unknown subwords.
        """
        assert isinstance(aWord, unicode)
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
                # Prüfen, ob Trennung explizit vorgegeben (Sonderfälle)
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
                    hwords[indx] = HyphenatedWord(words[indx], hyphenations=[])
            return HyphenatedWord.join(hwords)
        else:        
            return hwords[0] # Kann auch None sein.


if __name__=="__main__":
    h = ExplicitHyphenator("DE",5)
    h.add_entry("Bräutigam", "Bräu5ti5gam", "iso-8859-1")
    h.add_entries({u"Urinstinkt": u"Ur8instinkt",
                   u"Urinstinkte": u"Ur8instinkte",
                   u"Urinstinkten": u"Ur8instinkt3en",
                  }
                 )
    h.test(outfname="ExplicitLearn.html")
