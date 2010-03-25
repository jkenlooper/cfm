#!/usr/bin/env python
"""use cloudfile meta files as placeholders for cloud files"""

from optparse import OptionParser
import os
ACTION_ADD = 'add'
ACTION_GET_NEW = 'get-new'
ACTION_UPDATE = 'update'
ACTION_CLEAN = 'clean'
ACTION_DELETE = 'delete'
ACTION_STEAL = 'steal'

ACTIONS = (ACTION_ADD, ACTION_GET_NEW, ACTION_UPDATE, ACTION_CLEAN, ACTION_DELETE, ACTION_STEAL)


def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class File(object):
  """ a file that is located on the cloud and has a meta file locally """
  META_EXT = '.cloudfile_meta'
  META_CONTAINER_NAME = (30, 40)
  def __init__(self, path_to_file):
    self._file_name = os.path.basename(path_to_file) # basename?
    self._path_to_file = path_to_file
    self._meta_file = "%s%s" % (path_to_file, META_EXT)
    if os.path.exists(self._meta_file):
      f = open(self._meta_file, 'b')
      f.seek(META_CONTAINER_NAME[0])
      self.local_container_name = f.read(META_CONTAINER_NAME[1])
      f.close()
    elif os.path.exists(self._path_to_file):
      self.modified = 'today'
      self.hash = 'imahash'
    else: # this is very unlikely...
      print "error: '%s' doesn't exist and does not have a matching meta file", % self._path_to_file
      #TODO: raise a proper error
  
  def __del__(self):
    print "deleting"
    f = open(self._meta_file, 'b')
    #TODO: write out meta file here
    f.seek(META_CONTAINER_NAME[0])
    f.write(self.container_name)
    f.close()
    object.__del__(self)

  @Property
  def local_container_name():
    doc = "container name in the local meta file"
    def fget(self):
      return self._container_name
    def fset(self, container_name):
      #TODO: raise error if container_name is too big
      self._container_name = container_name
    return locals()

  def create_yaml(self, container_name, owner):
    """ create a new yaml file """
    self.container = container_name
    self.owner = owner
    self._modified_date = 'today' # compare local file hash with yaml hash and set new modified if different
    self._hash = 'imahash'
    #TODO: write yaml file

  def set_meta_from_yaml(self):
    """ send meta data to the cloud file object """
    #self.meta = self.yaml
    pass
  @Property
  def meta():
    doc = " meta data from the cloud "
    def fget(self):
      m = {} # connect to the cloud and retrieve meta data
      return m
    def fset(self, m):
      # connect to the cloud and set meta data to m
      pass
    return locals()

  def _set_meta(self, container_name, owner):
    """ set meta ... """

  @Property
  def container_name():
    doc = "name of the container in the cloud that this file is in."
    def fget(self):
      return self._container
    def fset(self, container_name):
      self._container_name = container_name
    return locals()
  
  @Property
  def owner():
    doc = "owner of the file"
    def fget(self):
      return self._owner
    def fset(self, owner_name):
      self._owner = owner_name
    return locals()

  def upload_to_cloud(self):
    """ add the file to the cloud """
    pass

class Controller(object):
  """ a Controller that works in a single directory """
  def __init__(self, owner_name, login_name, api_key):
    self.owner_name = owner_name
    #TODO: get a connection to the cloud using the api_key and login_name
  
  @Property
  def files():
    doc = "files to operate on. includes paths"
    def fget(self):
      return self._files
    def fset(self, files):
      self._files = files
    return locals()

  def add_files(self, container_name, file_list):
    """ add all the files in file_list and create a cloudfile.yaml for each. """
    #TODO: create container_name if it isn't in cloud
    for file_path in file_list:
      f = File(file_path)
      f.create_yaml(container_name, self.owner_name) # creates the yaml file
      f.set_meta_from_yaml() # add meta to the cloud file
      f.upload_to_cloud()
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
  parser.add_option("--container", "-c",
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

  def get_files(items, max_level=0):
    " walk through dir and retrieve all files "
    files = []
    for item in items:
      if os.path.isdir(item):
        for root, dir, file_names in os.walk(item, topdown=True):
          level = len(root.split('/'))
          if not max_level or max_level >= level:
            for f in file_names:
              files.append(os.path.join(root, f))
      else:
        files.append(item)
    return files


  max_level = 0
  if not options.recursive:
    max_level = 1
  files = get_files(args, max_level)
  owner_name, login_name, api_key = 'nothing', 'nothing', 'nothing'
  c = Controller(owner_name, login_name, api_key)
  c.files = files
  #TODO: do operation using the controller
  print ", ".join(files)



