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

"""Tests for dsrf.conformance.conformance_validators."""

import textwrap
import unittest
from dsrf.conformance import conformance_validators
from dsrf.conformance import error


class RowTest(object):

  def __init__(self, row_type, row_number):
    self.type = row_type
    self.row_number = row_number


class RowValidatorsTest(unittest.TestCase):

  def setUp(self):
    """Setting the nodes tree.

    Nodes structure:

     ugc profile
          |
        choice
        /    \
    sequence  C
      /\
     A  B
    """
    a = conformance_validators.Node(min_occurs=1, max_occurs=1,
                                    is_sequence=False, is_choice=False)
    a.set_row_type('a')
    b = conformance_validators.Node(min_occurs=1, max_occurs=1,
                                    is_sequence=False, is_choice=False)
    b.set_row_type('b')
    sequence = conformance_validators.Node(min_occurs=1, max_occurs=1,
                                           is_sequence=True, is_choice=False)
    sequence.add_child(a)
    sequence.add_child(b)
    c = conformance_validators.Node(min_occurs=1, max_occurs=1,
                                    is_sequence=False, is_choice=False)
    c.set_row_type('c')
    choice = conformance_validators.Node(min_occurs=1, max_occurs=float('inf'),
                                         is_sequence=False, is_choice=True)
    choice.add_child(sequence)
    choice.add_child(c)
    self.root = conformance_validators.Node(
        min_occurs=1, max_occurs=1, is_sequence=False, is_choice=False)
    self.root.add_child(choice)

  def test_validate_node_valid(self):
    one_valid_row = [RowTest('c', 4)]
    two_valid_rows = [RowTest('a', 1), RowTest('b', 2)]
    three_valid_rows = [RowTest('a', 1), RowTest('b', 2), RowTest('c', 3)]
    self.assertEqual(
        conformance_validators.validate_node(
            self.root, one_valid_row, index=0, block_number=4, file_number=3),
        1)
    self.assertEqual(
        conformance_validators.validate_node(self.root, two_valid_rows, 0, 3,
                                             2), 2)
    self.assertEqual(
        conformance_validators.validate_node(
            self.root, three_valid_rows, index=0, block_number=5,
            file_number=1), 3)

  def test_validate_node_invalid_row(self):
    one_invalid_rows = [RowTest('a', 5)]
    expected_error = textwrap.dedent(r"""
        Block 4 starting on row 5 in file number 8 is non-conformant\.

        First invalid row: 1 \(row 6 in input file\).

        Expected structure:
        \[Sequence \(a and b\) or c\]\+
        Actual structure:
        \['a'\]
    """).lstrip()
    self.assertRaisesRegexp(error.BlockConformanceFailure, expected_error,
                            conformance_validators.validate_node, self.root,
                            one_invalid_rows, 0, 4, 8)

  def test_validate_node_invalid_rows(self):
    two_invalid_rows = [RowTest('a', 6), RowTest('d', 7)]
    expected_error = textwrap.dedent(r"""
        Block 5 starting on row 6 in file number 8 is non-conformant\.

        First invalid row: 1 \(row 7 in input file\).

        Expected structure:
        \[Sequence \(a and b\) or c\]\+
        Actual structure:
        \['a', 'd'\]
    """).lstrip()
    self.assertRaisesRegexp(error.BlockConformanceFailure, expected_error,
                            conformance_validators.validate_node, self.root,
                            two_invalid_rows, 0, 5, 8)

  def test_node_to_string(self):
    self.assertEqual(str(self.root), '[Sequence (a and b) or c]+')


if __name__ == '__main__':
  unittest.main()
