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

"""The errors of the dsrf parsing library."""


class ValidationError(Exception):
  pass


class XsdParsingFailure(ValidationError):
  """Schema parsing failure Exception."""

  def __init__(self, xsd_file_name, error):
    super(XsdParsingFailure, self).__init__()
    self.xsd_file_name = xsd_file_name
    self.error = error

  def __str__(self):
    return 'Unexpected error while parsing the xsd file %s (error = %s).' % (
        self.xsd_file_name, self.error)


class RowValidationFailure(ValidationError):

  def __init__(self, row_number, file_name, error):
    super(RowValidationFailure, self).__init__()
    self.row_number = row_number
    self.file_name = file_name
    self.error = error

  def __str__(self):
    return 'Row number %s (file=%s) is invalid (error=%s).' % (
        self.row_number, self.file_name, self.error)


class CellValidationFailure(ValidationError):
  """Cell validation failure Exception."""

  def __init__(self, cell_name, row_number, file_name, block_number, cell_value,
               expected_value):
    super(CellValidationFailure, self).__init__()
    self.cell_name = cell_name
    self.row_number = row_number
    self.file_name = file_name
    self.block_number = block_number
    self.cell_value = cell_value
    self.expected_value = expected_value

  def _get_block_string(self):
    # Block number is not populated for HEAD/FOOT rows.
    if self.block_number:
      return 'Block: %s, ' % self.block_number
    return ''

  def __str__(self):
    return (
        'Cell "%s" contains invalid value "%s". Value was expected to be %s. '
        '[%sRow: %d, file=%s].' % (
            self.cell_name, self.cell_value, self.expected_value,
            self._get_block_string(), self.row_number, self.file_name))


class BadUnicodeError(CellValidationFailure):
  """Value was not valid UTF-8."""

  def __init__(self, cell_name, row_number, file_name, block_number, cell_value,
               error_detail):
    super(BadUnicodeError, self).__init__(
        cell_name, row_number, file_name, block_number, cell_value, None)
    self.error_detail = error_detail

  def __str__(self):
    return (
        'Cell "%s" contained a non-utf8 string: "%r". Error detail: "%s". '
        '[%sRow: %d, file=%s].' % (
            self.cell_name, self.cell_value, self.error_detail,
            self._get_block_string(), self.row_number, self.file_name))


class RequiredCellMissing(CellValidationFailure):
  """Value is required but was not present."""

  def __str__(self):
    return (
        'Cell "%s" is required. Value was expected to be %s. '
        '[%sRow: %d, file=%s].' % (
            self.cell_name, self.expected_value,
            self._get_block_string(), self.row_number, self.file_name))


class ReportValidationFailure(ValidationError):
  """Report cross-files validation failure Exception."""

  def __init__(self, error):
    super(ReportValidationFailure, self).__init__()
    self.error = error

  def __str__(self):
    return self.error


class FileNameValidationFailure(ReportValidationFailure):
  """File name validation failure Exception."""

  def __init__(self, file_name, error):
    super(FileNameValidationFailure, self).__init__(error)
    self.file_name = file_name

  def __str__(self):
    return 'File %s has invalid filename (error = %s).' % (
        self.file_name, self.error)


class FileNameValidationWarning(FileNameValidationFailure):
  """Non-fatal file name validation failure Exception."""
  pass
