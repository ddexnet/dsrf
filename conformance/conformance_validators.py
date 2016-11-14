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

"""Validates the blocks (rows type and order) in a Flat File."""

from dsrf.conformance import error


QUANTIFIER_STR = """\n
Quantifiers:
\t* Zero or more occurrences
\t+ One or more occurrences
\t? Zero or one occurrences
"""


class Node(object):
  """A conformance Node.

  Can be the root, a sequence, a choice or an element.
  The nodes are parsed from the XSD profile file.
  """

  def __init__(
      self, min_occurs=1, max_occurs=1, is_sequence=False, is_choice=False):
    self.min_occurs = min_occurs
    self.max_occurs = max_occurs
    self.is_sequence = is_sequence
    self.is_choice = is_choice
    self.children = []
    self.row_type = None

  def add_child(self, child):
    self.children.append(child)

  def set_row_type(self, row_type):
    self.row_type = row_type

  def get_quantification(self):
    """Summarizes min_occurs and max_occurs in a quantifier.

    Returns:
      '?' for zero or one occurrences
      '*' for zero or more occurrences
      '+' for one or more occurrences
    """
    if self.min_occurs == 0:
      if self.max_occurs == 1:
        return '?'
      return '*'
    if self.min_occurs == 1 and self.max_occurs > 1:
      return '+'
    return ''

  def __str__(self):
    """Presents the node as a string.

    Returns:
      The node's string representation.
    """
    str_to_return = ''
    if self.is_sequence:
      str_to_return = 'Sequence (%s)' % ' and '.join(
          [str(child) for child in self.children])
    elif self.is_choice:
      str_to_return = '[%s]' % ' or '.join(
          [str(child) for child in self.children])
    elif self.row_type:
      str_to_return = self.row_type
    else:
      str_to_return = str(self.children[0])

    return str_to_return + self.get_quantification()


def _is_row_matching(rows, index, node_type):
  return index < len(rows) and node_type == rows[index].type


def single_choice(children, rows, index, block_number, file_number):
  for child in children:
    validated_rows = validate_node(child, rows, index, block_number,
                                   file_number)
    # Since this is a choice, we're happy as soon as we find the first match.
    if validated_rows:
      return validated_rows
  return 0


def single_sequence(children, rows, index, block_number, file_number):
  """Validate a single iteration of a sequence node.

  Args:
    children: The sequence node's children to validate.
    rows: A list of row_pb2.Row objects to test for conformance.
    index: The current row number we test for conformance.
    block_number: The block number we validate.
    file_number: The file number we validate.

  Returns:
    The number of rows which were validated.
  """
  total_validated_rows = 0
  for child in children:
    validated_rows = validate_node(child, rows, index, block_number,
                                   file_number)
    index += validated_rows
    # We bail when we find the first required node that is not present.
    if not validated_rows and child.min_occurs > 0:
      return 0
    total_validated_rows += validated_rows
  return total_validated_rows


def validate_node(node, rows, index, block_number, file_number):
  """Validates that the given rows match the given node.

  Args:
    node: A node conformance object.
    rows: A list of row_pb2.Row objects to conform.
    index: The current row number we conform.
    block_number: The block number we validate.
    file_number: The file number we validate.

  Returns:
    The number of rows that matched the node.
  """
  # Base case, leaf node.
  if not node.children:
    occurs = 0
    while occurs < node.max_occurs:
      if _is_row_matching(rows, index, node.row_type):
        index += 1
        occurs += 1
      else:
        if occurs < node.min_occurs:
          return 0
        return occurs
    return occurs
  # Choice.
  elif node.is_choice:
    occurs = 0
    rows_validated = 0
    while occurs < node.max_occurs:
      nr_rows_validated = single_choice(
          node.children, rows, index, block_number, file_number)
      rows_validated += nr_rows_validated
      if not nr_rows_validated:
        if occurs < node.min_occurs:
          return 0
        return rows_validated
      index += nr_rows_validated
      occurs += 1
    return rows_validated
  # Sequence.
  elif node.is_sequence:
    rows_validated = 0
    occurs = 0
    while occurs < node.max_occurs:
      nr_rows_validated = single_sequence(
          node.children, rows, index, block_number, file_number)
      if not nr_rows_validated:
        if occurs < node.min_occurs:
          return 0
        return rows_validated
      occurs += 1
      index += nr_rows_validated
      rows_validated += nr_rows_validated
    return rows_validated
  # Root element (for the profile).
  else:
    child = node.children[0]
    rows_validated = validate_node(
        child, rows, index, block_number, file_number)
    if rows and rows_validated != len(rows):
      raise error.BlockConformanceFailure(
          rows[index].row_number, rows_validated, block_number, file_number,
          node, rows)
    return rows_validated
