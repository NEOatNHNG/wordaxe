#Copyright ReportLab Europe Ltd. 2000-2004
#see license.txt for license details
#history http://www.reportlab.co.uk/cgi-bin/viewcvs.cgi/public/reportlab/trunk/reportlab/test/test_paragraphs.py
# tests some paragraph styles

import unittest
from tests.utils import makeSuiteForClasses, outputfile, printLocation

from reportlab.platypus import Paragraph, SimpleDocTemplate, XBox, Indenter, XPreformatted
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import red, black, navy, white, green
from reportlab.lib.randomtext import randomText
from reportlab.rl_config import defaultPageSize # @UnresolvedImport

from wordaxe.rl.styles import getSampleStyleSheet, ParagraphStyle
from wordaxe.rl.NewParagraph import Paragraph

(PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize

try:
    import wordaxe
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.DCWHyphenator import DCWHyphenator
    wordaxe.hyphRegistry['DE'] = DCWHyphenator('DE', 5)
except ImportError:
    print("could not import wordaxe - try to continue WITHOUT hyphenation!")

def myFirstPage(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(red)
    canvas.setLineWidth(5)
    canvas.line(66,72,66,PAGE_HEIGHT-72)
    canvas.setFont('Times-Bold',24)
    canvas.drawString(108, PAGE_HEIGHT-54, "TESTING NBSP")
    canvas.setFont('Times-Roman',12)
    canvas.drawString(4 * inch, 0.75 * inch, "First Page")
    canvas.restoreState()


def myLaterPages(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(red)
    canvas.setLineWidth(5)
    canvas.line(66,72,66,PAGE_HEIGHT-72)
    canvas.setFont('Times-Roman',12)
    canvas.drawString(4 * inch, 0.75 * inch, "Page %d" % doc.page)
    canvas.restoreState()


class NBSPTestCase(unittest.TestCase):
    "Test NBSP (eyeball-test)."

    def test0(self):
        """Test...

        The story should contain...

        Features to be visually confirmed by a human being are:

            1. ...
            2. ...
            3. ...
        """

        story = []

        #need a style
        styNormal = ParagraphStyle('normal')
        
        ### The next two lines are important for hyphenation
        styNormal.language = 'DE'
        styNormal.hyphenation = True

        text = "Dr.&nbsp;M&#252;ller-L&#252;denscheid aus Hohenlimburg sagt: 'Hohenlimburg&nbsp;statt&nbsp;Hagen'!";
        text = [ ("*"*i + " " + text) for i in range(40)]
        story.append(
            Paragraph(" ".join(text), styNormal))
        template = SimpleDocTemplate(outputfile('test_nbsp.pdf'),
                                     showBoundary=1)
        template.build(story,
            onFirstPage=myFirstPage, onLaterPages=myLaterPages)


def makeSuite():
    return makeSuiteForClasses(NBSPTestCase)


#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()