#!/usr/bin/env python
"""use cloudfile meta files as placeholders for cloud files"""

from optparse import OptionParser
import os
import struct # for meta file packing/unpacking
import time
import datetime
import hashlib
import ConfigParser
import cloudfiles
ACTION_ADD = 'add'
ACTION_GET_NEW = 'get-new'
ACTION_UPDATE = 'update'
ACTION_CLEAN = 'clean'
ACTION_DELETE = 'delete'
ACTION_STEAL = 'steal'

ACTIONS = (ACTION_ADD, ACTION_GET_NEW, ACTION_UPDATE, ACTION_CLEAN, ACTION_DELETE, ACTION_STEAL)

META_EXT = '.cfm' # cloud file meta | cruddy file management
HASH_LEN = 32 # len(hashlib.md5("yup").hexdigest())
PACK_TIME_FORMAT = "%Y%j%H%M" #year dayofyear hour minute
MODIFIED_LEN = 11 # len(time.strftime(PACK_TIME_FORMAT, time.gmtime()))
CONTAINER_NAME_LEN = 30
OWNER_NAME_LEN = 10
URI_LEN = 100
META_FMT = "%is %is %is %is" % (HASH_LEN, MODIFIED_LEN, OWNER_NAME_LEN, CONTAINER_NAME_LEN)
META_FMT_PUBLIC = "%s %is" % (META_FMT, URI_LEN) # (network byte order), hash (padding), date, owner, container, uri


def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class File(object):
  """ a file that is located on the cloud and has a meta file locally """

  def __init__(self, path_to_file):
    self._file_name = os.path.basename(path_to_file) # basename?
    self._path_to_file = path_to_file
    self._meta_file = "%s%s" % (path_to_file, META_EXT)
    self._uri = ""
    if os.path.exists(self._meta_file):
      self._unpack()
    elif os.path.exists(self._path_to_file):
      self._local_modified = time.strftime(PACK_TIME_FORMAT, time.gmtime(os.stat(self._path_to_file).st_mtime))
      lf = open(self._path_to_file, 'r')
      self.local_hash = hashlib.md5(lf.read()).hexdigest()
      lf.close()
    else: # this is very unlikely...
      print "error: '%s' doesn't exist and does not have a matching meta file" % self._path_to_file
      #TODO: raise a proper error
  
  def __del__(self):
    print "deleting"
    self._pack()
    #super(File, self).__del__(self)

  def _pack(self):
    "write the File attributes to the local meta file"
    f = open(self._meta_file, 'w')
    if self.uri != "":
      p = struct.pack(META_FMT_PUBLIC, self.local_hash, self._local_modified, self.local_owner_name, self.local_container_name, self.uri)
    else:
      p = struct.pack(META_FMT, self.local_hash, self._local_modified, self.local_owner_name, self.local_container_name)
    f.write(p)
    f.close()
  def _unpack(self):
    "read the File attributes from the local meta file"
    f = open(self._meta_file, 'r')
    p = f.read()
    f.close()
    if len(p) == struct.calcsize(META_FMT):
      self.local_hash, self._local_modified, self._local_owner_name, self._local_container_name = struct.unpack(META_FMT, p)
    elif len(p) == struct.calcsize(META_FMT_PUBLIC):
      self.local_hash, self._local_modified, self._local_owner_name, self._local_container_name, self._uri = struct.unpack(META_FMT_PUBLIC, p)
    else:
      #TODO: raise proper error
      print "corrupt meta file"

    if os.path.exists(self._path_to_file):
      lf = open(self._path_to_file, 'r')
      self.local_hash = hashlib.md5(lf.read()).hexdigest() # use binascii.hexlify(self.local_hash) to compare with remote
      lf.close()

  @Property
  def local_modified():
    doc = "local modified time as formatted date time"
    def fget(self):
      return time.asctime(time.strptime(self._local_modified, PACK_TIME_FORMAT))
    return locals()
  @Property
  def local_container_name():
    doc = "container name in the local meta file"
    def fget(self):
      return self._container_name
    def fset(self, container_name):
      #TODO: raise error if container_name is too big
      self._container_name = container_name[:CONTAINER_NAME_LEN]
    return locals()

  @Property
  def local_owner_name():
    doc = "local owner name"
    def fget(self):
      return self._local_owner_name
    def fset(self, owner_name):
      self._local_owner_name = owner_name
    return locals()

  @Property
  def uri():
    doc = "location of file if public"
    def fget(self):
      return self._uri
    def fset(self, uri):
      self._uri = uri
    return locals()

  def create_meta_file(self, container_name, owner):
    """ create a new meta file """
    self.local_container_name = container_name
    self.local_owner_name = owner
    self._local_modified = time.strftime(PACK_TIME_FORMAT, time.gmtime(os.stat(self._path_to_file).st_mtime))
    lf = open(self._path_to_file, 'r')
    self.local_hash = hashlib.md5(lf.read()).hexdigest() # use binascii.hexlify(self.local_hash) to compare with remote
    lf.close()

  def set_remote_meta(self):
    """ send meta data to the cloud file object """
    print "set remote meta"
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

  def upload_to_cloud(self):
    """ add the file to the cloud """
    pass

class Controller(object):
  """ a Controller that handles the actions """
  def __init__(self, owner_name, connection):
    self.owner_name = owner_name
    self.connection = connection
  
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
      f.create_meta_file(container_name, self.owner_name)
      f.set_remote_meta() # add meta to the cloud file
      f.upload_to_cloud()
    print "done"
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
      default="local.cfg",
      help="specify a local connection config file. already reads from: ~/.cloudfile.cfg, ~/cloudfile.cfg")
  parser.add_option("--recursive", "-R",
      action="store_true",
      help="For any directories listed in args find all the *.cfm files")
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
  config = ConfigParser.SafeConfigParser()
  config.read("~/.cloudfile.cfg", "~/cloudfile.cfg", options.config)
  conn = cloudfiles.get_connection(config.get('server', 'login_name'), config.get('server', 'api_key'), servicenet=config.getboolean('server', 'servicenet'))
  #TODO: handle errors for the config.
  c = Controller(config.get('local', 'owner_name'), conn)
  c.files = files
  if options.action == ACTION_ADD:
    c.add_files(options.container, c.files)
  elif options.action == ACTION_GET_NEW:
    pass
  else:
    pass
  #TODO: do operation using the controller
  print ", ".join(files)



