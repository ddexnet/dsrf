# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for dsrf.conformance.xsd_profile_parser."""

from os import path
import unittest
from xml.etree import ElementTree

from dsrf.conformance import xsd_profile_parser


class XsdProfileParserTest(unittest.TestCase):

  def setUp(self):
    ugc_profile_path = path.join(
        path.dirname(__file__), '../testdata/nodes/profile_node.xml')
    self.profile_parser = xsd_profile_parser.XSDProfileParser(ugc_profile_path)

  def test_create_node(self):
    """Tests the create node method.

    Test structure:
         choice
         /    \
       SY03  SY04
    """
    choice_element = path.join(
        path.dirname(__file__), '../testdata/nodes/choice_node.xml')
    tree = ElementTree.parse(choice_element)
    root = tree.getroot()
    actual_node = self.profile_parser.create_node(root)
    self.assertEquals(str(actual_node), '[SY03 or SY04]+')

  def test_get_profile_node(self):
    """Tests the get_profile_node method.

    Test structure:
                    block root
                         |
                        seq
                  /      |    \     \
             choice   choice   SU03  LI01
              /   |      |   \
           seq1  AS02  RU01  RU02
          /   \
       AS01   MW01
    """
    actual_profile_node = self.profile_parser.parse_profile_from_xsd(
        'Ugc')
    self.assertEquals(
        'Sequence ([Sequence (AS01 and MW01*) or AS02] and [RU01 or RU02]+ and'
        ' SU03+ and LI01*)',
        str(actual_profile_node))


if __name__ == '__main__':
  unittest.main()
