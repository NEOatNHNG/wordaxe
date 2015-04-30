#!/usr/bin/env python

"""Test for compatibility with multibuilds made by rst2pdf."""

import unittest
from io import BytesIO

from tests.utils import makeSuiteForClasses, printLocation

try:
    from rst2pdf.createpdf import RstToPdf
except ImportError:
    RstToPdf = None

text = """
Rst2Pdf MultiBuild Test Case For Wordaxe
========================================

Blah. Blah.

Blah. Blah. Blah.

Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah.

Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah.

Blah.

  - Blah.
  - Blah.
  - Blah.

Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah.

  - Blah.
  - Blah.
  - Blah.

Blah. Blah. Blah.

Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah. Blah.

Blah. Blah. Blah.

.. contents::

Test Section
------------

Blah. Blah. Blah.

Blah. Blah. Blah. Blah. Blah.

Blah. Blah. Blah.
"""

blah = 'The quick brown fox jumps over the lazy dog'

text = text.replace('Blah', blah)


class MultiBuildTestCase(unittest.TestCase):
    """Test rst2pdf muiltibuild"""

    def test_rst2pdf(self):

        assert RstToPdf, 'rst2pdf not installed - cannot test compatibility.'

        rst2pdf = RstToPdf(breaklevel=0)

        rst2pdf.styles['heading1'].spaceBefore = 36

        buffer = BytesIO()

        rst2pdf.createPdf(text, output=buffer)

        pdf = buffer.getvalue()
        buffer.close()

        assert b'ReportLab generated PDF document' in pdf
        assert b'Rst2Pdf MultiBuild Test Case For Wordaxe' in pdf
        assert b'Test Section' in pdf
        assert blah.encode() in pdf


def makeSuite():
    return makeSuiteForClasses(MultiBuildTestCase)

if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()
