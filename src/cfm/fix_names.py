#!/usr/bin/env python
from optparse import OptionParser
import os
import re

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

if __name__ == "__main__":
  parser = OptionParser(version="%prog 0.1", description="rename files to only have alphanumeric and dashes")
  parser.add_option("--dry_run", "-n",
      action="store_true",
      help="print the command instead of running it.")

  (options, args) = parser.parse_args()

  for filepathname in args:
    if os.path.exists(filepathname):
      (head, tail) = os.path.split(filepathname)
      tail = tail.lower()
      (file, ext) = os.path.splitext(tail)
      file = re.sub("[^a-z0-9-_]+", '_', file)
      newfilepathname = "%s%s%s" % (head, file, ext)
      if filepathname != newfilepathname:
        ##esc_filepathname = re.sub(r"""([$"'!])""", '\1', filepathname)
        #esc_filepathname = re.sub(r"""(?P<e>[$"'!])""", """//\g<e>""", filepathname)
        #esc_filepathname = esc_filepathname.replace("//", """\x5c""")
        command = r'mv "%s" %s%s%s' % (filepathname, head, file, ext)
        if options.dry_run:
          print command
        else:
          os.system(command)
