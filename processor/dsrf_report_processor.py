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

"""Process the block objects, by a custom logic."""
import sys

from google.protobuf import message as message_mod
from dsrf import constants
from dsrf.proto import block_pb2


class BaseReportProcessor(object):
  """The Report processor base class.

  Inherit from the base class and override the 'process_report' method in order
  to add your custom logic.
  """

  def __init__(self, block_processor):
    self.block_processor = block_processor
    # Will be updated every time a HEAD block comes in.
    self.current_filename = None

  def update_filename(self, block):
    if block.type == block_pb2.HEAD:
      self.current_filename = block.filename

  def read_blocks_from_queue(self):
    """Returns a generator of the blocks in the queue.

    Override this method if you wish to change the queue (blocks transformation)
    form.

    Yields:
      Each yield is a single block object (block_pb2.Block).
    """
    message_lines = []
    for line in sys.stdin:
      if constants.QUEUE_DELIMITER in line:
        block = block_pb2.Block()
        try:
          block.ParseFromString('\n'.join(message_lines))
        except message_mod.DecodeError:
          sys.stderr.write(
              'ERROR: Can not read protocol buffer from queue. Is '
              'human_readable perhaps set to true? I am not a human. '
              'Aborting...\n')
          sys.exit(-1)

        yield block
        message_lines = []
      else:
        message_lines.append(line.rstrip('\n'))

  def process_report(self):
    for block in self.read_blocks_from_queue():
      self.update_filename(block)
      self.block_processor.process_block(block)
