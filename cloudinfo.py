#!/usr/bin/env python
'''cloud info script'''

import cloudfiles
import ConfigParser
from optparse import OptionParser
import os.path

if __name__ == "__main__":
  parser = OptionParser(version="%prog 0.1", description="show general info on the cloud")
  parser.add_option("--verbose", "-v",
      action="store_true",
      help="show all objects in the container")
  parser.add_option("--config",
      action="store",
      type="string",
      default=os.path.join(os.path.expanduser("~"), "cloudfile.cfg"),
      help="specify a cloud connection config file.")
  parser.add_option("--container", "-c",
      action="store",
      type="string",
      help="show info on just this container")

  (options, args) = parser.parse_args()

  config = ConfigParser.SafeConfigParser()
  config.read(options.config)
  conn = cloudfiles.get_connection(config.get('server', 'login_name'), config.get('server', 'api_key'), servicenet=config.getboolean('server', 'servicenet'))

  if options.container:
    containers = [conn.get_container(options.container),]
  else:
    containers = conn.get_all_containers()

  for container in containers:
    out = container.name
    if container.is_public():
      out = "%s %s" % (out, container.public_uri())
    try:
      if options.verbose:
        #c = conn.get_container(container.name)
        c = container
        objects = c.get_objects()
        obj_names = []
        for storage_object in objects:
          obj_names.append(storage_object.name)
        out = "%s : \n %s" % (out, "  ".join(obj_names))

    except NoSuchContainer:
      print "no such container: %s" % container.name

    print out
