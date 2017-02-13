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

"""Parses the config files into cells and rows validators."""

from os import path
from xml.etree import ElementTree

import cell_validators

from dsrf import constants
from dsrf import error

# A map between the xsd types to their cell validator objects.
VALIDATOR_TYPES_MAP = {
    'xs:integer': cell_validators.IntegerValidator,
    'xs:string': cell_validators.StringValidator,
    'xs:decimal': cell_validators.DecimalValidator,
    'xs:boolean': cell_validators.BooleanValidator,
    'xs:duration': cell_validators.DurationValidator,
    'xs:dateTime': cell_validators.DateTimeValidator,
    }


class DsrfSchemaParser(object):
  """The schema parser object.

  Contains the parsing methods of the config files.

  Attributes:
    _fixed_string_values: A dictionary of {types: [valid values]}
    dsrf_xsd_file_name: The schema file to parse.
    simple_types_map: A dictionary of {simple type name: ElementTree.Element}
  """

  def __init__(self, avs_xsd_file_name, dsrf_xsd_file_name):
    self._fixed_string_values = None
    if avs_xsd_file_name:
      self._fixed_string_values = self.parse_fixed_strings(avs_xsd_file_name)
    self.dsrf_xsd_file_name = dsrf_xsd_file_name
    self.avs_xsd_file_name = avs_xsd_file_name
    self.simple_types_map = {}

  def is_complex_type(self, element):
    return 'type' not in element.attrib

  def get_cell_name(self, element):
    return element.attrib['name']

  def get_simple_cell_type(self, element):
    return element.attrib['type']

  def get_cell_validator(self, cell_name, cell_type, required, repeated,
                         logger):
    """Creates a cell validator object by the given cell name.

    Args:
      cell_name: The cell name (from the schema file).
      cell_type: The cell type (from the schema file).
      required: True if the cell is mandatory.
      repeated: True if the cell is repeated.
      logger: The library logger.

    Returns:
      cell_validator object.
    """
    # Primitive types.
    if cell_type in VALIDATOR_TYPES_MAP:
      return VALIDATOR_TYPES_MAP[cell_type](cell_name, logger, required,
                                            repeated)
    # Simple types.
    if cell_type.startswith(constants.DSRF_TYPE_PREFIX):
      cell_type = cell_type.split(':')[-1]
    if cell_type in self.simple_types_map:
      if (self.simple_types_map[cell_type][1][0].tag ==
          constants.XSD_TAG_PREFIX + 'pattern'):
        return cell_validators.PatternValidator(
            self.simple_types_map[cell_type][1][0].attrib['value'], cell_name,
            logger, required, repeated)
    # AVS types.
    cell_type = cell_type.replace(constants.FIXED_STRING_PREFIX, '')
    if cell_type in self._fixed_string_values:
      return cell_validators.FixedStringValidator(
          self._fixed_string_values[cell_type], cell_name, logger, required,
          repeated)
    raise error.XsdParsingFailure(
        path.basename(self.dsrf_xsd_file_name), 'The cell type %s does not '
        'exist in the provided configuration files. Please make sure you use '
        'the right files and version.' % cell_type)

  def is_required(self, element):
    min_occurs = element.attrib.get('minOccurs', '1')
    return int(min_occurs) == 1

  def is_repeated(self, element):
    if 'maxOccurs' in element.attrib.keys():
      return element.attrib['maxOccurs'].lower() == 'unbounded'
    return False

  def is_pattern(self, element):
    return element[1][0][0].tag == constants.XSD_TAG_PREFIX + 'pattern'

  def get_cell_pattern(self, element):
    return element[1][0][0].attrib['value']

  def get_fixed_string_values(self, root):
    """Parses the allowed values to a dictionary of {types: [valid values]}.

    If an IndexError/AttributeError/KeyError is raised in this method, your
    schema file didn't match the expected structure. For valid schema files,
    please check the '/schemas' directory.

    Args:
      root: An ElementTree.element object of the avs file root.

    Returns:
      A dictionary of {types: [valid values]}
      (eg. {'RecordType':['SY02', 'MW01']}), without union types.
    """
    fixed_string_dict = {}
    for element in root:
      if element.tag == constants.XSD_TAG_PREFIX + 'simpleType':
        element_name = element.attrib['name']
        fixed_string_dict[element_name] = []
        try:
          for allowed_value in element[1]:
            fixed_string_dict[element_name].append(
                allowed_value.attrib['value'])
        except (IndexError, KeyError):
          raise error.XsdParsingFailure(
              self.avs_xsd_file_name,
              'Malformed AVS xsd element: %s.' % element_name)
    return fixed_string_dict

  def parse_union_fixed_strings(self, root, fixed_string_dict):
    """Parses the 'xs:union' type fixed strings.

    An AVS type with a union element, can have all the values of it's
    memberTypes. For example the allowed values of a type with the following
    union: <xs:union memberTypes="avs:a avs:b avs:c"/> are the allowed values of
    a, b and c.

    If an IndexError/AttributeError/KeyError is raised in this method, your
    schema file didn't match the expected structure. For valid schema files,
    please check the '/schemas' directory.

    Args:
      root: An ElementTree.element object of the avs file root.
      fixed_string_dict: A dictionary of {types: [valid values]}
                         (without union types).

    Returns:
      A dictionary of {types: [valid values]}
      (eg. {'RecordType':['SY02', 'MW01']}), include the union types.
    """
    for element in root:
      if element.tag == constants.XSD_TAG_PREFIX + 'simpleType':
        element_name = element.attrib['name']
        if 'union' in element[1].tag:
          member_types = element[1].attrib['memberTypes'].replace(
              constants.FIXED_STRING_PREFIX, '')
          for member_type in member_types.split():
            fixed_string_dict[element_name].extend(
                fixed_string_dict[member_type])
    return fixed_string_dict

  def parse_fixed_strings(self, avs_file_name):
    """Parses the avs file to a dictionary of {types: [valid values]}.

    Args:
      avs_file_name: avs file path to parse.

    Returns:
      A dictionary of {types: [valid values]}
      (eg. {'RecordType':['SY02', 'MW01']}).
    """
    tree = ElementTree.parse(avs_file_name)
    root = tree.getroot()
    fixed_string_dict = self.get_fixed_string_values(root)
    return self.parse_union_fixed_strings(root, fixed_string_dict)

  def get_dsrf_xsd_cells(self, row, logger):
    """Parses the given row tag to cell validator objects.

    Args:
      row: XML tag object of the row to parse.
      logger: The library logger.

    Returns:
      A list of cell validator objects of the row.
    """
    cells = []
    for sub_row in row:
      if sub_row.tag == constants.XSD_TAG_PREFIX + 'sequence':
        for element in sub_row:
          if element.tag == constants.XSD_TAG_PREFIX + 'element':
            cell_name = self.get_cell_name(element)
            if self.is_complex_type(element):
              if self.is_pattern(element):
                cells.append(
                    cell_validators.PatternValidator(
                        self.get_cell_pattern(element), cell_name, logger,
                        self.is_required(element), self.is_repeated(element)))
              else:
                # Complex type but not a pattern, raise error.
                raise error.XsdParsingFailure(
                    self.dsrf_xsd_file_name,
                    'Unexpected complexType '+ element[1][0][0].tag)
            else:
              # Not a complex type, must be simple type.
              cell_type = self.get_simple_cell_type(element)
              cells.append(
                  self.get_cell_validator(
                      cell_name, cell_type, self.is_required(element),
                      self.is_repeated(element), logger))
    return cells

  def parse_simple_types(self, root):
    for element in root:
      if element.tag == constants.XSD_TAG_PREFIX + 'simpleType':
        type_name = element.attrib['name']
        self.simple_types_map[type_name] = element

  def parse_complex_types(self, root, logger):
    """Parses the complex types to row validators.

    Args:
      root: ElementTree.element object of the schema file root.
      logger: The library logger.

    Returns:
      A dictionary of rows and cells validators objects.
    """
    rows = {}
    for element in root:
      try:
        if (element.tag == constants.XSD_TAG_PREFIX + 'complexType' and
            constants.is_row_type(element.attrib['name'])):
          row_type = element.attrib['name'][
              len(constants.VALID_ROW_TYPE_PREFIX):]
          row_cells = self.get_dsrf_xsd_cells(element, logger)
          rows[row_type] = row_cells
      except error.ValidationError as e:
        logger.error(e)
    return rows

  def get_avs_location_from_root(self, root):
    """Inspects the root tag of the profile XSD to find the AVS xsd version."""
    for child in root:
      if child.tag == constants.XSD_TAG_PREFIX + 'import':
        if child.attrib.get('namespace') == constants.AVS_XSD_NAMESPACE:
          schema_location = child.attrib['schemaLocation']
          unused_directory, avs_version = path.split(
              path.split(schema_location)[0])
          return constants.get_xsd_file('avs', avs_version)
    raise error.XsdParsingFailure(
        self.dsrf_xsd_file_name,
        'No AVS import found (namespace = %s).' % constants.AVS_XSD_NAMESPACE)

  def parse_xsd_file(self, logger):
    """Parses an xsd file as a dictionary of {row_name: cells validators list}.

    The row name is taken from the RecordType cell which is mandatory in every
    row (eg. "FileHeader", "MusicalWorkRecord"). The cells validators is an
    ordered list of the cells in the required row.

    Args:
      logger: The library logger.

    Returns:
      A dictionary of rows and cells validators objects.
    """
    tree = ElementTree.parse(self.dsrf_xsd_file_name)
    root = tree.getroot()
    if not self.avs_xsd_file_name:
      self.avs_xsd_file_name = self.get_avs_location_from_root(root)
    self._fixed_string_values = self.parse_fixed_strings(self.avs_xsd_file_name)
    self.parse_simple_types(root)
    rows = self.parse_complex_types(root, logger)
    logger.raise_if_fatal_errors_found()
    return rows
