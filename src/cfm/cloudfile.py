#!/usr/bin/env python
"""use cloudfile meta files as placeholders for cloud files"""

#cfm - Cruddy File Management for rackspace cloudfiles
#Copyright (C) 2012  Jake Hickenlooper
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


from shutil import move
import os
import os.path
import time
import datetime
import hashlib
import ConfigParser

import cloudfiles
from cloudfiles.errors import NoSuchContainer, NoSuchObject
from progressbar import FileTransferSpeed, ETA, Bar, Percentage, ProgressBar

META_EXT = '.cfm' # cloud file meta | cruddy file management
HASH_LEN = 32 # len(hashlib.md5("yup").hexdigest())
PACK_TIME_FORMAT = "%Y%j%H%M" #year dayofyear hour minute

#cloudfile metadata keys
OWNER = "owner"
MODIFIED = "modified"
HASH = "hash"
COMMENT = "comment"

def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class File(object):
  """ a file that is located on the cloud and has a meta file locally """

  def __init__(self, path_to_file):
    self._deleted_meta_file = False
    self._file_name = os.path.basename(path_to_file) # basename?
    self._path_to_file = path_to_file
    self._meta_file = "%s%s" % (path_to_file, META_EXT)
    if os.path.exists(self._meta_file):
      self._unpack()
    elif os.path.exists(self._path_to_file):
      self._local_modified = time.strftime(PACK_TIME_FORMAT, time.gmtime(os.stat(self._path_to_file).st_mtime))
      lf = open(self._path_to_file, 'r')
      self.local_hash = hashlib.md5(lf.read()).hexdigest()
      lf.close()
    else: # creating a new meta file.
      self._local_modified = 'unknown'
      self.local_hash = 'unknown'
      self._local_owner_name = 'unknown'
  
  def __del__(self):
    self._pack()
    #super(File, self).__del__(self)

  def _pack(self):
    "write the File attributes to the local meta file"
    if not self._deleted_meta_file:
      f = open(self._meta_file, 'w')
      f.write(self.local_hash)
      f.write("\n")
      f.write(self._local_modified)
      f.write("\n")
      f.write(self.local_owner)
      f.write("\n")
      f.write(self.container_name)
      f.write("\n")
      f.close()
  def _unpack(self):
    "read the File attributes from the local meta file"
    f = open(self._meta_file, 'r')
    lines = [l.strip() for l in f.readlines()]
    f.close()
    if len(lines) == 4:
      self.local_hash, self._local_modified, self._local_owner_name, self._container_name = lines
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
    def fset(self, t):
      #TODO: check for proper format
      self._local_modified = t
    return locals()

  @Property
  def file_name():
    doc = "file name (not settable)"
    def fget(self):
      return self._file_name
    return locals()

  @Property
  def file_path():
    doc = "file path (not settable)"
    def fget(self):
      return self._path_to_file
    return locals()

  @Property
  def container_name():
    doc = "container name in the local meta file"
    def fget(self):
      return self._container_name
    def fset(self, container_name):
      #TODO: raise error if container_name is too big
      self._container_name = container_name
    return locals()

  @Property
  def local_owner():
    doc = "local owner name"
    def fget(self):
      return self._local_owner_name
    def fset(self, owner_name):
      self._local_owner_name = owner_name
    return locals()

  @Property
  def cloudfile():
    doc = "rackspace cloud object"
    def fget(self):
      return self._cloudfile
    def fset(self, c):
      self._cloudfile = c
    return locals()

  @Property
  def remote_modified():
    doc = "remote modified date"
    def fget(self):
      return time.asctime(time.strptime(self._cloudfile.metadata["modified"], PACK_TIME_FORMAT))
    return locals()

  @Property
  def remote_owner():
    doc = "remote owner name"
    def fget(self):
      return self._cloudfile.metadata["owner"]
    def fset(self, owner_name):
      self._cloudfile.metadata["owner"] = owner_name
    return locals()
  
  @Property
  def remote_hash():
    doc = "remote hash of file"
    def fget(self):
      return self._cloudfile.metadata["hash"]
    return locals()

  @Property
  def uri():
    doc = "location of file if container is public"
    def fget(self):
      if self._cloudfile.container.is_public():
        return "%s/%s" % (self._cloudfile.container.public_uri(), self._file_name)
      return False
    return locals()

  def create_meta_file(self, container_name, owner):
    """ create a new meta file """
    self.container_name = container_name
    self.local_owner = owner
    self._local_modified = time.strftime(PACK_TIME_FORMAT, time.gmtime(os.stat(self._path_to_file).st_mtime))
    lf = open(self._path_to_file, 'r')
    self.local_hash = hashlib.md5(lf.read()).hexdigest() # use binascii.hexlify(self.local_hash) to compare with remote
    lf.close()

  def set_remote_meta(self):
    """ send meta data to the cloud file object """
    try:
      self._cloudfile.sync_metadata()
    except:
      print "error in set_remote_meta\n"
  
  def delete_meta(self):
    """ delete meta file """
    os.remove(self._meta_file)
    self._deleted_meta_file = True # prevents writing of meta file on close

  def upload_to_cloud(self):
    """ add the file to the cloud """
    #f = open(self._path_to_file, 'r')
    widgets = [FileTransferSpeed(),' <<<', Bar(), '>>> ', Percentage(),' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=os.path.getsize(self._path_to_file))
    pbar.start()
    def progress(transferred, size):
      pbar.update(transferred)
      if transferred >= size:
        pbar.finish()
        print
    try:
      self._cloudfile.load_from_filename(self._path_to_file, verify=False, callback=progress)
    except:
      print "error loading: %s" % self._path_to_file
    #self._cloudfile.send(f)
    m = self._local_modified
    self._cloudfile.metadata["modified"] = m
    h = self.local_hash
    self._cloudfile.metadata["hash"] = h
    #TODO: use a callback to track progress of upload

  def download_from_cloud(self, file_path=None):
    widgets = [FileTransferSpeed(),' <<<', Bar(), '>>> ', Percentage(),' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=self._cloudfile.size)
    pbar.start()
    def progress(transferred, size):
      pbar.update(transferred)
      if transferred >= size:
        pbar.finish()
        print
    if not file_path:
      file_path = self._path_to_file
    print "downloading: %s" % file_path
    self._cloudfile.save_to_filename(file_path, progress)

  def read_from_cloud(self):
    #print "reading: %s" % self._path_to_file
    return self._cloudfile.read()

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
      self._files = []
      self._meta_files = []
      for f in files:
        n, ext = os.path.splitext(f)
        if ext == META_EXT and f not in self._meta_files:
          self._meta_files.append(f)
        elif ext != META_EXT:
          self._files.append(f)
          if "%s%s" % (f, META_EXT) not in self._meta_files:
            self._meta_files.append("%s%s" % (f, META_EXT))
          
    return locals()

  def add_files(self, container_name):
    """ add all the files in file_list and create a meta file for each. """
    cloudcontainer = self.connection.create_container(container_name)
    for file_path in self._files:
      filename = os.path.basename(file_path)
      cloudfile = cloudcontainer.create_object(filename)
      f = File(file_path)
      f.cloudfile = cloudfile
      f.create_meta_file(container_name, self.owner_name)
      f.remote_owner = self.owner_name
      f.upload_to_cloud()
      f.set_remote_meta() # syncs meta data to the cloud
      print "uploaded: %s" % file_path
  def download_new(self):
    """ compare the hashes and download new if different or not existant. """
    meta_files_grouped_by_container = {}
    for meta_file_path in [x for x in self._meta_files if os.path.isfile(x)]:
      file_path = meta_file_path[:len(meta_file_path) - len(META_EXT)]
      f = File(file_path)
      try:
        meta_files_grouped_by_container[f.container_name].append(f)
      except KeyError:
        meta_files_grouped_by_container[f.container_name] = []
        meta_files_grouped_by_container[f.container_name].append(f)

    total_files_to_download = count = len(self._meta_files)
    print "Total files to download: %i" % total_files_to_download
    for container_name in meta_files_grouped_by_container.keys():
      c = meta_files_grouped_by_container[container_name]
      try:
        cloudcontainer = self.connection.get_container(container_name)
        for f in c:
          try:
            cloudfile = cloudcontainer.get_object(f.file_name) #if not in cloud then mark it as deleted and remove the meta file
            f.cloudfile = cloudfile
            if ((f.local_hash != f.remote_hash) or not os.path.exists(f.file_path)):
              f.download_from_cloud()
              print "%i/%i" % (count, total_files_to_download)
            count -= 1
            f.local_owner = f.remote_owner
            # local_modified too?
            if f.uri:
              print f.uri
          except NoSuchObject:
            print "file: [%s] no longer exists on the cloud" % file_path
            f.delete_meta()
            print meta_file_path
            if os.path.exists(file_path):
              new_path = os.path.join(os.path.dirname(file_path), "deleted.%s" % filename)
              move(file_path, new_path)
      except NoSuchContainer:
        print "Container: [%s] doesn't exist on cloud" % f.container_name


    #for meta_file_path in self._meta_files:
    #  file_path = meta_file_path[:len(meta_file_path) - len(META_EXT)]
    #  filename = os.path.basename(file_path)
    #  f = File(file_path)
    #  try:
    #    cloudcontainer = self.connection.get_container(f.container_name)
    #    cloudfile = cloudcontainer.get_object(filename) #if not in cloud then mark it as deleted and remove the meta file
    #    f.cloudfile = cloudfile
    #    if ((f.local_hash != f.remote_hash) or not os.path.exists(file_path)):
    #      f.download_from_cloud()
    #    f.local_owner = f.remote_owner
    #    # local_modified too?
    #    if f.uri:
    #      print f.uri
    #  except NoSuchContainer:
    #    print "Container: [%s] doesn't exist on cloud" % f.container_name
    #  except NoSuchObject:
    #    print "file: [%s] no longer exists on the cloud" % file_path
    #    f.delete_meta()
    #    print meta_file_path
    #    if os.path.exists(file_path):
    #      new_path = os.path.join(os.path.dirname(file_path), "deleted.%s" % filename)
    #      move(file_path, new_path)


  def upload_new(self):
    """ Update any that are different. Any that are different and have a different owner; get a copy of the one on server and add "owner_name." in front of it. Any that no longer exist in the cloud rename the file with "deleted." in front of it. """
    for meta_file_path in self._meta_files:
      file_path = meta_file_path[:len(meta_file_path) - len(META_EXT)]
      filename = os.path.basename(file_path)
      f = File(file_path)
      try:
        cloudcontainer = self.connection.get_container(f.container_name)
        cloudfile = cloudcontainer.get_object(filename) #if not in cloud then mark it as deleted and remove the meta file
        f.cloudfile = cloudfile
        if (f.local_owner != f.remote_owner) or (self.owner_name != f.remote_owner):
          remote_owner_path = os.path.join(os.path.dirname(file_path), "%s.%s" % (f.remote_owner, filename))
          print "file: %s has a different owner on cloud then local owner. downloading file as: %s" % (file_path, remote_owner_path)
          f.download_from_cloud(file_path=remote_owner_path)
        elif (f.local_hash != f.remote_hash) and os.path.exists(file_path):
          f.upload_to_cloud()
          f.set_remote_meta() # syncs meta data to the cloud
          print "updating cloud file: %s" % file_path

      except NoSuchContainer:
        print "Container: [%s] doesn't exist on cloud" % f.container_name
      except NoSuchObject:
        print "file: [%s] no longer exists on the cloud"
        f.delete_meta()
        if os.path.exists(file_path):
          new_path = os.path.join(os.path.dirname(file_path), "deleted.%s" % filename)
          move(file_path, new_path)

  def get_file(self, container_name):
    """ get/download file/s based on the name and container and generate a meta file for each. """
    #TODO: add directory to download files too?
    for file_path in self._files:
      filename = os.path.basename(file_path)
      f = File(file_path)
      f.container_name = container_name
      try:
        cloudcontainer = self.connection.get_container(f.container_name)
        cloudfile = cloudcontainer.get_object(filename)
        f.cloudfile = cloudfile
        f.download_from_cloud()

        f.create_meta_file(container_name, self.owner_name)

      except NoSuchContainer:
        print "Container: [%s] doesn't exist on cloud" % f.container_name
      except NoSuchObject:
        print "file: [%s] no longer exists on the cloud"

  def cat_file(self, container_name):
    """ cat file/s based on the name and container and generate a meta file for each. """
    for file_path in self._files:
      filename = os.path.basename(file_path)
      f = File(file_path)
      f.container_name = container_name
      try:
        cloudcontainer = self.connection.get_container(f.container_name)
        cloudfile = cloudcontainer.get_object(filename)
        f.cloudfile = cloudfile
        f._deleted_meta_file = True # prevents writing of meta file on close
        return f.read_from_cloud()

      except NoSuchContainer:
        print "Container: [%s] doesn't exist on cloud" % f.container_name
      except NoSuchObject:
        print "file: [%s] no longer exists on the cloud"


  def clean(self):
    """ delete files just from local directory and leave the meta file untouched """
    for file_path in self._files:
      filename = os.path.basename(file_path)
      if "%s%s" % (file_path, META_EXT) in self._meta_files:
        f = File(file_path)
        try:
          cloudcontainer = self.connection.get_container(f.container_name)
          cloudfile = cloudcontainer.get_object(filename)
          f.cloudfile = cloudfile
          if (f.local_owner != f.remote_owner):
            print "owners don't match; cannot clean file: %s " % file_path
          elif (f.local_hash != f.remote_hash):
            print "hash of files don't match; cannot clean file: %s " % file_path
          else:
            os.system("rm %s" % file_path)

        except NoSuchContainer:
          print "Container: [%s] doesn't exist on cloud" % f.container_name
        except NoSuchObject:
          print "file: [%s] no longer exists on the cloud" % file_path
          if os.path.exists(file_path):
            new_path = os.path.join(os.path.dirname(file_path), "deleted.%s" % filename)
            move(file_path, new_path)
  def delete(self):
    """ Remove files from cloud """
    for meta_file_path in self._meta_files:
      file_path = meta_file_path[:len(meta_file_path) - len(META_EXT)]
      filename = os.path.basename(file_path)
      f = File(file_path)
      try:
        cloudcontainer = self.connection.get_container(f.container_name)
        cloudfile = cloudcontainer.get_object(filename)
        f.cloudfile = cloudfile
        if (f.local_owner == f.remote_owner):
          cloudcontainer.delete_object(filename)
          f.delete_meta()
        if not cloudcontainer.list_objects():
          print "Deleting empty container: %s" % f.container_name
          self.connection.delete_container(f.container_name)
      except NoSuchContainer:
        print "Container: [%s] doesn't exist on cloud" % f.container_name
      except NoSuchObject:
        print "file: [%s] has already been removed from the cloud" % file_path
        f.delete_meta()
  def steal(self):
    """ set owner name for any files that have a different owner (use 'upload_new' afterwards to update the files) """
    for meta_file_path in self._meta_files:
      file_path = meta_file_path[:len(meta_file_path) - len(META_EXT)]
      filename = os.path.basename(file_path)
      f = File(file_path)
      try:
        cloudcontainer = self.connection.get_container(f.container_name)
        cloudfile = cloudcontainer.get_object(filename)
        f.cloudfile = cloudfile
        if (f.local_owner != self.owner_name):
          f.local_owner = self.owner_name
          f.remote_owner = self.owner_name
          f.set_remote_meta()
          print "stealing: %s" % file_path
      except NoSuchContainer:
        print "Container: [%s] doesn't exist on cloud" % f.container_name
      except NoSuchObject:
        print "file: [%s] no longer exists on the cloud" % file_path

  def get_meta_files(self, container, dir):
    """ create all the meta files for the container and place them in the directory specified in files """
    try:
      cloudcontainer = self.connection.get_container(container)
      if os.path.isdir(dir):
        for filename in cloudcontainer.list_objects():
          f = File(os.path.join(dir, filename))
          cloudfile = cloudcontainer.get_object(filename)
          f.cloudfile = cloudfile
          f.local_owner = f.remote_owner
          f.local_hash = f.remote_hash
          f.local_modified = f.cloudfile.metadata["modified"]
          f.container_name = container
          f.set_remote_meta()
    except NoSuchContainer:
      print "Container: [%s] doesn't exist on cloud" % container
    except NoSuchObject:
      print "file: [%s] no longer exists on the cloud" % filename
  
  def make_container_public(self, container, ttl=604800):
    """ make the container specified to be accessible from the public """
    try:
      cloudcontainer = self.connection.get_container(container)
      cloudcontainer.make_public(ttl=ttl)
    except NoSuchContainer:
      print "Container: [%s] doesn't exist on cloud" % container

  def make_container_private(self, container):
    """ make a container be private and no longer accessible from the public """
    try:
      cloudcontainer = self.connection.get_container(container)
      cloudcontainer.make_private()
    except NoSuchContainer:
      print "Container: [%s] doesn't exist on cloud" % container

  def set_referrer_restriction(self, container, url):
    """ set acl referrer restriction """
    try:
      cloudcontainer = self.connection.get_container(container)
      cloudcontainer.acl_referrer(url)
    except NoSuchContainer:
      print "Container: [%s] doesn't exist on cloud" % container

