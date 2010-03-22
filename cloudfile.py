#!/usr/bin/env python
"""use yaml files as placeholders for cloud files"""

from optparse import OptionParser
import yaml

ACTIONS = ('add', 'get-new', 'update', 'clean', 'delete', 'steal')

def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class File(object):
  """ a file that is located on the cloud and locally """
  def __init__(self, container_name, file_name):
    self._owner = 'someone'
    self._modified_date = 'today'
    self._hash = 'imahash'

  @Property
  def owner():
    doc = "owner of the file"
    def fget(self):
      return self._owner
    def fset(self, owner_name):
      self._owner = owner_name
    return locals()

if __name__ == "__main__" :
  parser = OptionParser(usage="%%prog --action [%s] [options] [files and or directories]" % "|".join(ACTIONS), version="%prog 0.1", description="add files to the cloud")

  parser.add_option("--action", "-a",
      action="store",
      type="choice",
      choices=ACTIONS,
      help="Specify what action to do with the files/directories listed. choices: %s" % ", ".join(ACTIONS))
  parser.add_option("--config", "-c",
      action="store",
      type="string",
      help="specify a different config file other then the default ~.cloudfile.config one.")
  parser.add_option("--recursive", "-R",
      action="store_true",
      help="For any directories listed in args find all the *.cloudfile.yaml")


  (options, args) = parser.parse_args()

  if not args :
    parser.error("No files or directories specified.")

