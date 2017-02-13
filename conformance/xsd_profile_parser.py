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

"""Parses a dsrf xsd file to conformance_validators.Node profile object."""

import sys

from xml.etree import ElementTree
from dsrf import constants
from dsrf import error
from dsrf.conformance import conformance_validators

PROFILE_NODE_TYPES = [constants.XSD_TAG_PREFIX + 'choice',
                      constants.XSD_TAG_PREFIX + 'sequence',
                      constants.XSD_TAG_PREFIX + 'element']


class XSDProfileParser(object):
  """Parses the xsd file into a conformance_validators.Node."""

  def __init__(self, dsrf_xsd_file_name):
    self.dsrf_xsd_file_name = dsrf_xsd_file_name
    self.complex_elements = {}

  def get_occurs_number(self, occurs_type, occurs_str):
    try:
      return int(occurs_str)
    except ValueError:
      raise error.XsdParsingFailure(
          self.dsrf_xsd_file_name,
          'The value "%s" is invalid as a %s. Expected an integer/"unbounded".'
          % (occurs_str, occurs_type))

  def get_max_occurs(self, node_element):
    max_occurs = node_element.attrib.get('maxOccurs', '1')
    if max_occurs == 'unbounded':
      return float('inf')
    return self.get_occurs_number('maxOccurs', max_occurs)

  def create_node(self, node_element):
    """Parses the node element to a conformance_validators.Node object.

    Args:
      node_element: ElementTree.Element object of a profile node type.

    Returns:
      A conformance_validators.Node object of the node element.
    """
    min_occurs = self.get_occurs_number(
        'minOccurs', node_element.attrib.get('minOccurs', '1'))
    max_occurs = self.get_max_occurs(node_element)
    is_sequence = node_element.tag == constants.XSD_TAG_PREFIX + 'sequence'
    is_choice = node_element.tag == constants.XSD_TAG_PREFIX + 'choice'
    node = conformance_validators.Node(
        min_occurs, max_occurs, is_sequence, is_choice)
    node_row_type = node_element.attrib.get('type', '')
    # Strip the DSRF prefix.
    if (node_row_type and not
        node_row_type.startswith(constants.DSRF_TYPE_PREFIX)):
      raise error.XsdParsingFailure(
          self.dsrf_xsd_file_name,
          'The element "%s" with type "%s" does not have the "%s" prefix. This '
          'is likely caused by the type of the parent element not being '
          'recognized as a valid row type. Please ensure that all row types in '
          'in the XSD start with the prefix "%s".'
          % (node_element.attrib.get('name'),
             node_row_type, constants.DSRF_TYPE_PREFIX,
             constants.VALID_ROW_TYPE_PREFIX))
    node_row_type = node_row_type.split(':')[-1]
    if node_row_type:
      if constants.is_row_type(node_row_type):
        node.set_row_type(node_row_type[len(constants.VALID_ROW_TYPE_PREFIX):])
        return node
      elif node_row_type in self.complex_elements:
        # All complex elements are sequences.
        node.is_sequence = True
        for element in self.complex_elements[node_row_type]:
          if element.tag in PROFILE_NODE_TYPES:
            node.add_child(self.create_node(element))
        return node
      else:
        raise error.XsdParsingFailure(
            self.dsrf_xsd_file_name,
            'The element "%s" with type "%s" does not exist in the dsrf xsd '
            'file "%s".'
            % (node_element.attrib.get('name'), node_row_type,
               self.dsrf_xsd_file_name))
    if node_element.getchildren():
      for child in node_element:
        if child.tag in PROFILE_NODE_TYPES:
          node.add_child(self.create_node(child))
    return node

  def create_profile_node(self, profile_element):
    """Creates the single root node of the tree of validators."""
    profile_node = conformance_validators.Node()
    for element in profile_element:
      if element.tag in PROFILE_NODE_TYPES:
        profile_node.add_child(self.create_node(element))
    return profile_node

  def is_profile_or_block(self, element):
    # If it's a complex type and it's not a Row definition, it must be a
    # profile or block.
    return (
        element.tag == constants.XSD_TAG_PREFIX + 'complexType' and
        not constants.is_row_type(element.attrib['name']))

  def is_profile(self, element):
    return (self.is_profile_or_block(element) and
            element.attrib['name'].lower().endswith('profile') and
            not element.attrib['name'].startswith(
                'ResourceIdentificationGroupingFor'))

  def _parse_elements(
      self, root, profile_name, parse_complex_types=True, parse_profile=True):
    """Parses specified children of the root tag."""
    profile_node = None
    profile_names = []
    for element in root:
      try:
        if parse_profile and self.is_profile(element):
          profile_names.append(element.attrib['name'])
        if self.is_profile_or_block(element):
          if element.attrib['name'].lower() == profile_name.lower() + 'block':
            if parse_profile:
              profile_node = self.create_profile_node(element)
          elif parse_complex_types:
            self.complex_elements[element.attrib['name']] = element
      except KeyError:
        raise error.XsdParsingFailure(
            self.dsrf_xsd_file_name,
            'Unexpected complexType without a name: %s' % element.__dict__)
    return profile_node, profile_names

  def parse_profile_from_xsd(self, profile_name):
    """Returns the conformance_validators of the profiles.

    Args:
      profile_name: The profile to parse.

    Returns:
      conformance_validators.Node object of the given profile.
    """
    tree = ElementTree.parse(self.dsrf_xsd_file_name)
    root = tree.getroot()
    # First we scan the file for complex types. This first scan allows elements
    # to be defined out-of-order.
    self._parse_elements(
        root, profile_name, parse_complex_types=True, parse_profile=False)
    # Now we just parse the profile definition.
    profile_node, profile_names = self._parse_elements(
        root, profile_name, parse_complex_types=False, parse_profile=True)
    if not profile_node:
      sys.stderr.write(
          'The profile you entered %s does not exist in the dsrf xsd file: %s. '
          'Valid profiles: %s\n'
          % (profile_name, self.dsrf_xsd_file_name, profile_names))
    return profile_node
