from optparse import OptionParser
import os
import os.path
import ConfigParser

import cloudfiles

import cloudfile

ACTION_ADD = 'add'
ACTION_DOWNLOAD_NEW = 'download_new'
ACTION_UPLOAD_NEW = 'upload_new'
ACTION_CLEAN = 'clean'
ACTION_DELETE = 'delete'
ACTION_STEAL = 'steal'
ACTION_GET_META_FILES = 'get_meta'
ACTION_GET_FILE = 'get_file'
ACTION_CAT_FILE = 'cat_file'

ACTIONS = (ACTION_ADD, ACTION_DOWNLOAD_NEW, ACTION_UPLOAD_NEW, ACTION_CLEAN, ACTION_DELETE, ACTION_STEAL, ACTION_GET_META_FILES, ACTION_GET_FILE, ACTION_CAT_FILE)

def main():
  parser = OptionParser(usage="%%prog --action [%s] [options] [files and or directories]" % "|".join(ACTIONS), version="%prog 0.1", description="add files to the cloud")

  parser.add_option("--action", "-a",
      action="store",
      type="choice",
      choices=ACTIONS,
      help="Specify what action to do with the files/directories listed. choices: %s" % ", ".join(ACTIONS))
  parser.add_option("--config",
      action="store",
      type="string",
      default=os.path.join(os.path.expanduser("~"), "cloudfile.cfg"),
      help="specify a cloud connection config file.")
  parser.add_option("--recursive", "-R",
      action="store_true",
      help="For any directories listed in args find all the files")
  parser.add_option("--container", "-c",
      action="store",
      type="string",
      help="Set the name of the container to work in")
  parser.add_option("--public",
      action="store_true",
      help="make the container public and publish to the CDN")
  parser.add_option("--ttl",
      action="store",
      type="int",
      help="Time in seconds when the public container should refresh it's cache")
  parser.add_option("--referrer",
      action="store",
      type="string",
      help="restrict by referrer for the container ( specify a url like http://example.com )")
  parser.add_option("--private",
      action="store_true",
      help="make the container private. This is the default.")

  (options, args) = parser.parse_args()

  if not args and not (options.public or options.private or options.referrer):
    parser.error("No files or directories specified.")

  if not options.action and not (options.public or options.private or options.referrer):
    parser.error("Must specify an action")
  elif not (options.public or options.private or options.referrer) and options.action == ACTION_ADD and not options.container:
    parser.error("Must set a container name")
  elif (options.public or options.private or options.referrer or options.action in (ACTION_GET_META_FILES, ACTION_GET_FILE, ACTION_CAT_FILE)) and not options.container:
    parser.error("Must specify a container name")
  elif options.ttl and not options.public:
    parser.error("Must set option --public as well")


  def get_files(items, max_level=0):
    " walk through dir and retrieve all files "
    files = []
    restricted_names = ('.svn',)
    for item in [x for x in items if x not in restricted_names]:
      if os.path.isdir(item):
        for root, dir, file_names in os.walk(item, topdown=True):
          if ('.svn' not in root):
            #print root
            level = len(root.split('/'))
            if not max_level or max_level >= level:
              for f in [x for x in file_names if x not in restricted_names]:
                #print "   %s" % f
                files.append(os.path.join(root, f))
      else:
        files.append(item)
    return files

  max_level = 0
  if not options.recursive:
    max_level = 1
  files = get_files(args, max_level)
  config = ConfigParser.SafeConfigParser()
  config.read(options.config)
  conn = cloudfiles.get_connection(config.get('server', 'login_name'), config.get('server', 'api_key'), servicenet=config.getboolean('server', 'servicenet'))
  #TODO: set up a seperate authorization server proxy thingy so it can handle multiple users more securely and won't need to share the api key.
  #TODO: handle errors for the config.
  c = cloudfile.Controller(config.get('local', 'owner_name'), conn)
  c.files = files
  if options.action == ACTION_ADD:
    c.add_files(options.container)
  elif options.action == ACTION_DOWNLOAD_NEW:
    c.download_new()
  elif options.action == ACTION_UPLOAD_NEW:
    c.upload_new()
  elif options.action == ACTION_CLEAN:
    c.clean()
  elif options.action == ACTION_DELETE:
    c.delete()
  elif options.action == ACTION_STEAL:
    c.steal()
  elif options.action == ACTION_GET_META_FILES:
    c.get_meta_files(options.container, args[0])
  elif options.action == ACTION_GET_FILE:
    c.get_file(options.container)
  elif options.action == ACTION_CAT_FILE:
    print c.cat_file(options.container)
  else:
    print "unknown action: %s" % options.action

  if options.public and not options.private:
    if options.ttl:
      c.make_container_public(options.container, ttl=options.ttl)
    else:
      c.make_container_public(options.container)
  elif options.private:
    c.make_container_private(options.container)

  if options.referrer:
    #TODO verify proper referrer string (can be blank to unset it?)
    c.set_referrer_restriction(options.container, options.referrer)

  #TODO: do operation using the controller


