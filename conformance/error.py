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

"""The errors in the conformance process."""


class BlockConformanceFailure(Exception):

  def __init__(self, line_number, block_number, file_number, node, rows):
    super(BlockConformanceFailure, self).__init__()
    self.line_number = line_number
    self.block_number = block_number
    self.file_number = file_number
    self.node = node
    self.rows = rows

  def __str__(self):
    return ('Block %d starting on row %d in file number %d is non-conformant.\n'
            'Expected structure:\n%s\n'
            'Actual structure:\n%s' % (
                self.block_number, self.line_number, self.file_number,
                self.node, [str(row.type) for row in self.rows]))


class CardinalityFailure(Exception):

  def __init__(self, block_number, file_number, error):
    super(CardinalityFailure, self).__init__()
    self.block_number = block_number
    self.file_number = file_number
    self.error = error

  def __str__(self):
    return ('Block number %s in the file number %s is not conformant (error= %s'
            '.).' % (self.block_number, self.file_number, self.error))
