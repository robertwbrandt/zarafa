#!/usr/bin/env python
"""
Script used to backup Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse
import xml.etree.ElementTree as ElementTree

args = {}
args['version'] = 0.3
args['file'] = '/srv/backup/brick-level-backup/backup.log'
encoding = "utf-8"

def command_line_args():
  global args

  parser = argparse.ArgumentParser(description=".",
                    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v', '--version',
                    action='version',
                    version="%(prog)s " + str(args['version']) + """
  Copyright (C) 2011 Free Software Foundation, Inc.
  License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
  This is free software: you are free to change and redistribute it.
  There is NO WARRANTY, to the extent permitted by law.
  Written by Bob Brandt <projects@brandt.ie>.\n """)
  parser.add_argument('-f', '--file',
                    required=False,
                    default=args['file'],
                    type=str,
                    action='store')
  args.update(vars(parser.parse_args()))

# Start program
if __name__ == "__main__":
  command_line_args()

  try:
    f = open(args['file'], 'r')
    out = f.read()
    f.close()
  except:
    exit('Unable to read file ' + str(args['file']))

  users = {}
  currentuser = ""
  for line in out.split('\n'):
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

  print '<?xml version="1.0" encoding="' + encoding + '"?>'
  print ElementTree.tostring(xml, encoding=encoding, method="xml")

  exit()
