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

from wordaxe.hyphen import HyphenatedWord
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

if __name__=="__main__":
    h = ExplicitHyphenator("DE",5)
    h.add_entry("Bräutigam", "Bräu5ti5gam", "iso-8859-1")
    h.add_entries({u"Urinstinkt": u"Ur8instinkt",
                   u"Urinstinkte": u"Ur8instinkte",
                   u"Urinstinkten": u"Ur8instinkt3en",
                  }
                 )
    h.test(outfname="ExplicitLearn.html")
