from optparse import OptionParser
import yaml

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
  parser = OptionParser(version="%prog 0.1", description="add files to the cloud")

  #TODO: set the action to a choice of actions to do
  parser.add_option("--action", "-a", action="store", type="string")

  (options, args) = parser.parse_args()


