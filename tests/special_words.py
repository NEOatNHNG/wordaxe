from wordaxe.plugins.PyHyphenHyphenator import *

if __name__=="__main__":
    h = PyHyphenHyphenator("de_DE",5)
    h.add_entries_from_file("special_words.lst")
    h.test(outfname="PyHyphenLearn.html")
