#!/usr/bin/env python
"""use yaml files as placeholders for cloud files"""

from optparse import OptionParser
import yaml
ACTION_ADD = 'add'
ACTION_GET_NEW = 'get-new'
ACTION_UPDATE = 'update'
ACTION_CLEAN = 'clean'
ACTION_DELETE = 'delete'
ACTION_STEAL = 'steal'

ACTIONS = (ADD, GET_NEW, UPDATE, CLEAN, DELETE, STEAL)

def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class File(object):
  """ a file that is located on the cloud and locally """
  def __init__(self, container_name, file_name):
    self._container = 'a_container'
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

class Controller(object):
  """ a Controller that works in a single directory """
  def __init__(self, owner_name, login_name, api_key, directory):
    self.owner_name = owner_name
    self.directory = directory
    #TODO: get a connection to the cloud using the api_key and login_name
  
  @Property
  def directory():
    doc = "directory to operate in"
    def fget(self):
      return self._directory
    def fset(self, dir):
      #TODO: check to see if the dir exists and is a directory
      self._directory = dir
    return locals()

  def add_files(self, container_name, file_list):
    """ add all the files in file_list and create a cloudfile.yaml for each. """
    pass
  def get_new(self):
    """ search for cloudfile.yaml files and compare the hashes and download new if different or not existant. """
    pass
  def update(self):
    """ Update any that are different. Any that are different and have a different owner; get a copy of the one on server and add "owner_name." in front of it. Any that no longer exist in the cloud rename the file with "deleted." in front of it. """
    pass
  def clean(self):
    """ delete files just from local directory and leave the yaml untouched """
    pass
  def delete_files(self, file_list):
    """ Remove files from cloud and local directory """
    pass
  def steal_files(self, file_list):
    """ any files that are different and have a different owner; replace file in cloud and change owner. """
    pass


if __name__ == "__main__":
  parser = OptionParser(usage="%%prog --action [%s] [options] [files and or directories]" % "|".join(ACTIONS), version="%prog 0.1", description="add files to the cloud")

  parser.add_option("--action", "-a",
      action="store",
      type="choice",
      choices=ACTIONS,
      help="Specify what action to do with the files/directories listed. choices: %s" % ", ".join(ACTIONS))
  parser.add_option("--config",
      action="store",
      type="string",
      help="specify a different config file other then the default ~.cloudfile.config one.")
  parser.add_option("--recursive", "-R",
      action="store_true",
      help="For any directories listed in args find all the *.cloudfile.yaml")
  parser.container("--container", "-c",
      action="store",
      type="string",
      help="Set the name of the container to work in")


  (options, args) = parser.parse_args()

  if not args:
    parser.error("No files or directories specified.")

  if not options.action:
    parser.error("Must specify an action")
  elif options.action == ACTION_ADD and not options.container:
    parser.error("Must set a container name when adding files")

