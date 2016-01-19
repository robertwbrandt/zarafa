#!/usr/bin/env python
"""
Script used to backup Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, subprocess, os
import xml.etree.ElementTree as ElementTree

args = {}
args['version'] = 0.3
args['threads'] = 4
args['location'] = '/srv/backup/brick-level-backup'
args['log'] = None
args['xml'] = None
encoding = "utf-8"
zarafaBackup = '/usr/sbin/zarafa-backup'

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
  parser.add_argument('-l', '--location',
                    required=False,
                    default=args['location'],
                    type=str,
                    action='store')
  parser.add_argument('--log',
                    required=False,
                    type=str,
                    action='store')
  parser.add_argument('--xml',
                    required=False,
                    type=str,
                    action='store')  
  parser.add_argument('-t', '--threads',
                    required=False,
                    default=args['threads'],
                    type=int,
                    action='store')  
  args.update(vars(parser.parse_args()))

  if not os.path.isdir(str(args['location'])):
    exit('The path specified (' + str(args['location']) + ') does not exist.')
  if not args['log']:
    args['log'] = os.path.join(args['location'], 'backup.log')
  if not args['xml']:
    args['log'] = os.path.join(args['location'], 'backup.xml')




# Start program
if __name__ == "__main__":
  command_line_args()

  f = open(args['log'], 'w')
  cmd = [ zarafaBackup, '-a', '-v', '-t', str(args['threads']), '-o', args['location'] ]
  users = {}
  currentuser = ""
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
