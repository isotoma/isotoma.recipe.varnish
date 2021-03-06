"""Test setup for isotoma.recipe.varnish.
"""

import os, re
import pkg_resources

import zc.buildout.testing

import unittest
import zope.testing
from zope.testing import doctest, renormalizing


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('isotoma.recipe.varnish', test)
    zc.buildout.testing.install('isotoma.recipe.gocaptain', test)
    zc.buildout.testing.install('zope.testing', test)
    zc.buildout.testing.install('Cheetah', test)
    zc.buildout.testing.install('Markdown', test)


checker = renormalizing.RENormalizing([
    zc.buildout.testing.normalize_path,
    (re.compile('#![^\n]+\n'), ''),
    (re.compile('-\S+-py\d[.]\d(-\S+)?.egg'),'-pyN.N.egg',),
    (re.compile('\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}\|'), 'YYYY/MM/DD HH:MM:SS|'),
    ])


def test_suite():
    return unittest.TestSuite([
       doctest.DocFileSuite('doctests/varnish.txt',
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=doctest.ELLIPSIS, checker=checker),
       ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
