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


from os import path
import unittest
from xml.etree import ElementTree

from dsrf import constants
from dsrf import dsrf_logger
from dsrf import error
from dsrf.parsers import cell_validators
from dsrf.parsers import dsrf_schema_parser


class SchemaParserBaseTest(unittest.TestCase):

  def setUp(self):
    avs_filename = path.join(path.dirname(__file__), '../testdata/avs.xsd')
    xsd_filename = path.join(path.dirname(__file__),
                             '../testdata/sales-reporting-flat.xsd')
    self.dsrf_schema_parser = dsrf_schema_parser.DsrfSchemaParser(
        avs_filename, xsd_filename)
    self.logger = dsrf_logger.DSRFLogger(__name__, '/tmp/example.log', True)

  def test_parse_fixed_strings(self):
    filename = path.join(path.dirname(__file__), '../testdata/avs.xsd')
    expected_dict = {
        'RecordType': ['HEAD', 'FOOT', 'FHEA', 'FFOO', 'SY01', 'SY02', 'SY03',
                       'SY04', 'RE01', 'RE02', 'RE03', 'AS01', 'AS02', 'AS03',
                       'MW01', 'CU01', 'SU01', 'SU02', 'SU03', 'SU04', 'RU01',
                       'RU02', 'LI01'],
        'UseType': ['AsPerContract', 'Broadcast', 'ConditionalDownload',
                    'ContentInfluencedStream', 'Display', 'Download'],
        'ProfileId': ['BasicAudioProfile', 'UGCProfile', 'AudioVisualProfile',
                      'RoyaltyReportingProfile', 'BroadcastReportingProfile']}
    self.assertEquals(self.dsrf_schema_parser.parse_fixed_strings(filename),
                      expected_dict)

  def test_parse_fixed_string_union_valid(self):
    filename = path.join(path.dirname(__file__),
                         '../schemas/avs/current/avs.xsd')
    self.assertIsNotNone(
        self.dsrf_schema_parser.parse_fixed_strings(filename)['TerritoryCode'])
    self.assertIsNotNone(
        self.dsrf_schema_parser.parse_fixed_strings(filename)['CurrencyCode'])
    self.assertIsNotNone(
        self.dsrf_schema_parser.parse_fixed_strings(filename)[
            'CurrentTerritoryCode'])

  def test_parse_fixed_string_union_invalid(self):
    filename = path.join(
        path.dirname(__file__), '../testdata/avs_schema_parser_test.xsd')
    self.assertRaisesRegexp(
        KeyError, '', self.dsrf_schema_parser.parse_fixed_strings, filename)

  def test_get_cell_validator(self):
    """Tests the successful path."""
    expected_valid_values = [
        'AsPerContract', 'Broadcast', 'ConditionalDownload',
        'ContentInfluencedStream', 'Display', 'Download']
    integer_validator = self.dsrf_schema_parser.get_cell_validator(
        'FileNumber', 'xs:integer', True, False, self.logger)
    string_validator = self.dsrf_schema_parser.get_cell_validator(
        'MessageID', 'xs:string', True, False, self.logger)
    boolean_validator = self.dsrf_schema_parser.get_cell_validator(
        'HasCaptioning', 'xs:boolean', True, False, self.logger)
    decimal_validator = self.dsrf_schema_parser.get_cell_validator(
        'RightSharePercentage', 'xs:decimal', True, False, self.logger)
    duration_validator = self.dsrf_schema_parser.get_cell_validator(
        'PT123645', 'xs:duration', True, False, self.logger)
    fixed_string_validator = self.dsrf_schema_parser.get_cell_validator(
        'UseType', 'avs:UseType', True, False, self.logger)
    self.dsrf_schema_parser.simple_types_map['ddex_IsoDate'] = (
        [[], [ElementTree.Element(tag=constants.XSD_TAG_PREFIX + 'pattern',
                                  attrib={'value': 'pattern'})]])
    simple_type_validator = self.dsrf_schema_parser.get_cell_validator(
        '2015-02', 'dsrf:ddex_IsoDate', True, False, self.logger)

    self.assertIsInstance(string_validator, cell_validators.StringValidator)
    self.assertIsInstance(integer_validator, cell_validators.IntegerValidator)
    self.assertIsInstance(boolean_validator, cell_validators.BooleanValidator)
    self.assertIsInstance(decimal_validator, cell_validators.DecimalValidator)
    self.assertIsInstance(duration_validator, cell_validators.DurationValidator)
    self.assertIsInstance(fixed_string_validator,
                          cell_validators.FixedStringValidator)
    self.assertEquals(fixed_string_validator.valid_values,
                      expected_valid_values)
    self.assertIsInstance(
        simple_type_validator, cell_validators.PatternValidator)

  def test_get_cells(self):
    xsd_filename = path.join(path.dirname(__file__),
                             '../testdata/sales-reporting-flat.xsd')
    tree = ElementTree.parse(xsd_filename)
    root = tree.getroot()
    for element in root:
      # Testing a single row, FileHeader, that contains all the exist
      # validators.
      if (element.tag == constants.XSD_TAG_PREFIX + 'complexType' and
          element.attrib['name'] == 'FileHeader'):
        row_cells = self.dsrf_schema_parser.get_dsrf_xsd_cells(
            element, self.logger)
        # RecordType
        self.assertIsInstance(
            row_cells[0], cell_validators.FixedStringValidator)
        # MessageID
        self.assertIsInstance(row_cells[1], cell_validators.StringValidator)
        # FileNumber
        self.assertIsInstance(row_cells[2], cell_validators.IntegerValidator)
        # NumberOfFiles
        self.assertIsInstance(row_cells[3], cell_validators.IntegerValidator)

  def test_get_cell_validator_handles_typo(self):
    """Tests a case of typo mistake in the file."""
    xsd_filename = path.join(path.dirname(__file__),
                             '../testdata/wrong_format.xsd')
    tree = ElementTree.parse(xsd_filename)
    root = tree.getroot()
    for element in root:
      # Testing a single row, FileHeader, that contains all the exist
      # validators.
      if (element.tag == constants.XSD_TAG_PREFIX + 'complexType' and
          element.attrib['name'] == 'FileHeader'):
        self.assertRaisesRegexp(
            error.XsdParsingFailure, 'Unexpected error while parsing the xsd '
            'file sales-reporting-flat.xsd \\(error = The cell type xs:stringg '
            'does not exist in the provided configuration files. Please make '
            'sure you use the right files and version.\\).',
            self.dsrf_schema_parser.get_dsrf_xsd_cells, element, self.logger)

  def test_parse_xsd_file_not_exist(self):
    """Tests a case of xsd file not exist."""
    avs_filename = path.join(path.dirname(__file__), '../testdata/avs.xsd')
    schema_parser = dsrf_schema_parser.DsrfSchemaParser(avs_filename, '')
    self.assertRaisesRegexp(
        IOError, 'No such file or directory: \'\'',
        schema_parser.parse_xsd_file, self.logger)

  def test_parse_xsd_file_valid_row_types_in_a_specific_row(self):
    """Tests the expected cells in a specific row."""
    rows_validators = self.dsrf_schema_parser.parse_xsd_file(self.logger)
    expected_su02_validators = [
        cell_validators.FixedStringValidator({}, 'RecordType', self.logger,
                                             True, False),
        cell_validators.StringValidator('BlockId', self.logger, True, False),
        cell_validators.StringValidator('SalesTransactionId', self.logger, True,
                                        False),
        cell_validators.StringValidator('TransactedReleaseOrResource',
                                        self.logger, True, False),
        cell_validators.StringValidator('CommercialModelType', self.logger,
                                        True, False),
        cell_validators.FixedStringValidator({}, 'UseType', self.logger, True,
                                             False),
        cell_validators.StringValidator('Territory', self.logger, True, False),
        cell_validators.StringValidator('ServiceDescription', self.logger,
                                        False, False),
        cell_validators.BooleanValidator('IsRoyaltyBearing', self.logger, True,
                                         False),
        cell_validators.IntegerValidator('NumberOfStreams', self.logger, True,
                                         False),
        cell_validators.StringValidator('Currency', self.logger, False, False),
        cell_validators.DecimalValidator('PriceConsumerPaidExcSalesTax',
                                         self.logger, False, False),
        cell_validators.StringValidator('PromotionalActivity', self.logger,
                                        False, False),
        cell_validators.BooleanValidator('PreviewAvailable', self.logger, False,
                                         False),
    ]
    for actual_cell, expected_cell in zip(
        rows_validators['SU02'], expected_su02_validators):
      self.assertIsInstance(actual_cell, expected_cell.__class__)
      self.assertEquals(actual_cell.cell_name, expected_cell.cell_name,
                        self.logger)
      self.assertEquals(actual_cell.required, expected_cell.required)
      self.assertEquals(actual_cell.repeated, expected_cell.repeated)


if __name__ == '__main__':
  unittest.main()
