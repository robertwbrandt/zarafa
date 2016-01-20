#!/usr/bin/env python
"""
Script used to backup Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, textwrap
import subprocess
import xml.etree.ElementTree as ElementTree

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "../common" ) ) )
import brandt
sys.path.pop()

version = 0.3
args = {}
args['threads'] = 4
args['location'] = '/srv/backup/brick-level-backup'
args['log'] = None
args['xml'] = None
encoding = "utf-8"
zarafaBackup = '/usr/sbin/zarafa-backup'

class customUsageVersion(argparse.Action):
  def __init__(self, option_strings, dest, **kwargs):
    self.__version = str(kwargs.get('version', ''))
    self.__prog = str(kwargs.get('prog', os.path.basename(__file__)))
    self.__row = int(kwargs.get('max', brandt.getTerminalSize()[0]))
    self.__exit = int(kwargs.get('exit', 0))
    super(customUsageVersion, self).__init__(option_strings, dest, nargs=0)
  def __call__(self, parser, namespace, values, option_string=None):
    # print('%r %r %r' % (namespace, values, option_string))
    if self.__version:
      print self.__prog + " " + self.__version
      print "Copyright (C) 2013 Free Software Foundation, Inc."
      print "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>."
      version  = "This program is free software: you can redistribute it and/or modify "
      version += "it under the terms of the GNU General Public License as published by "
      version += "the Free Software Foundation, either version 3 of the License, or "
      version += "(at your option) any later version."
      print textwrap.fill(version, self.__row)
      version  = "This program is distributed in the hope that it will be useful, "
      version += "but WITHOUT ANY WARRANTY; without even the implied warranty of "
      version += "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
      version += "GNU General Public License for more details."
      print textwrap.fill(version, self.__row)
      print "\nWritten by Bob Brandt <projects@brandt.ie>."
    else:
      print "Usage: " + self.__prog + " [-l LOCATION] [-t THREADS] [--log LOG] [--xml XML]"
      print "Script used to backup Zarafa Mailboxes via brick-level-backup.\n"
      print "Options:"
      options = []
      options.append(("-h, --help",              "Show this help message and exit"))
      options.append(("-v, --version",           "Show program's version number and exit"))
      options.append(("-l, --location LOCATION", "Backup location"))
      options.append(("-t, --threads THREADS",   "Number of threads to use. (Default: 4)"))
      options.append(("    --log LOG",           "Log file"))
      options.append(("    --xml XML",           "XML log file"))
      length = max( [ len(option[0]) for option in options ] )
      for option in options:
        description =  textwrap.wrap(option[1], (self.__row - length - 5))
        print "  " + option[0].ljust(length) + "   " + description[0]
        for n in range(1,len(description)): print " " * (length + 5) + description[n]
    exit(self.__exit)

def command_line_args():
  global args, version

  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('-v', '--version', action=customUsageVersion, version=version, max=80)
  parser.add_argument('-h', '--help', action=customUsageVersion)
  parser.add_argument('-l', '--location',
                    required=False,
                    default=args['location'],
                    type=str,
                    action='store')
  parser.add_argument('-t', '--threads',
                    required=False,
                    default=args['threads'],
                    type=int,
                    action='store')
  parser.add_argument('--log',
                    required=False,
                    type=str,
                    action='store')
  parser.add_argument('--xml',
                    required=False,
                    type=str,
                    action='store')
  args.update(vars(parser.parse_args()))

  if not os.path.isdir(str(args['location'])):
    exit('The path specified (' + str(args['location']) + ') does not exist.')
  if not args['log']:
    args['log'] = os.path.join(args['location'], 'backup.log')
  if not args['xml']:
    args['xml'] = os.path.join(args['location'], 'backup.xml')

# Start program
if __name__ == "__main__":
  command_line_args()

  cmd = [ zarafaBackup, '-a', '-v', '-t', str(args['threads']), '-o', args['location'] ]
  users = {}
  currentuser = ""
  print "Running the command: " + " ".join(cmd)
  print "Log File:", args['log']
  print "XML File:", args['xml']

  exit()

  f = open(args['log'], 'w')
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  for line in p.stdout:
    print line.strip('\n')
    f.write(line)

    tmp = line.split('[')
    if len(tmp) == 3:
      tmp = [ str(s).strip() for s in tmp[2].split(']',1) ]
      if tmp[0] == "info":
        tmp = str(tmp[1]).lower().rsplit(" ",1)
        if tmp[0] in ['starting backup of user', 'starting incremental backup for user', 'starting full backup for user']:
          currentuser = tmp[1]
          if not users.has_key(currentuser):
            users[currentuser] = {}

      elif tmp[0] == "fatal":
        if not users[currentuser].has_key('error'):
          users[currentuser]['error'] = []
        users[currentuser]['error'].append(tmp[1])

      elif tmp[0] == "notice":
        tmp = str(tmp[1]).split(' ')
        if len(tmp) > 4 and tmp[:3] == ['Backup','of','user']:
          users[str(tmp[3]).lower()]['done'] = ' '.join(tmp)

  for user in [ k for k in users.keys() if users[k] == {} ]:
    users[user]['error'] = ['Backup of user ' + user + ' failed!']

  errorUsers = str( len( [ k for k in users.keys() if users[k].has_key('error') ] ) )

  xml = ElementTree.Element('zarafa-backup', attrib={'errors':errorUsers})
  for user in sorted(users.keys()):
    attrib = {'name':user}
    if users[user].has_key('done'):
      attrib['done'] = users[user]['done']
    if users[user].has_key('error'):
      attrib['errors'] = str( len( users[user]['error'] ) )
    u = ElementTree.SubElement(xml, 'user', attrib=attrib)
    if users[user].has_key('error'):
      for error in users[user]['error']:
        e = ElementTree.SubElement(u, 'error')
        e.text = error

  p.wait()
  f.close()

  f = open(args['xml'], 'w')
  f.write( '<?xml version="1.0" encoding="' + encoding + '"?>\n' )
  f.write( ElementTree.tostring(xml, encoding=encoding, method="xml") )
  f.close()

  exit()
