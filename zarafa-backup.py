#!/usr/bin/env python
"""
Script used to backup Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, os, subprocess, datetime
import xml.etree.ElementTree as ElementTree

args = {}
args['output'] = "text"
args['version'] = 0.3

args['location'] = '/srv/backup/brick-level-backup'
args['log'] = ''
args['threads'] = 4

zarafaAdmin = '/usr/sbin/zarafa-admin'
zarafaBackup = '/usr/sbin/zarafa-backup'
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
  parser.add_argument('-o', '--output',
                    required=False,
                    default=args['output'],
                    choices=['text', 'xml'],
                    help='Display output type.')
  parser.add_argument('-l', '--location',
                    required=False,
                    default=args['location'],
                    type=str,
                    action='store')  
  parser.add_argument('--log',
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


# Start program
if __name__ == "__main__":
  command_line_args()
  print args

  p = subprocess.Popen([zarafaAdmin, '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = p.returncode
  if err or rc:
    exit(err)

  for user in sorted([ str(s.strip().split('\t')[0]).lower() for s in str(out).split('\n')[4:] if s ]):
    dateStr = str(datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y:')).ljust(26)

    print dateStr + str('[zarafa-backup] [ notice]').rjust(36) + ' Starting backup of user ' + user
    # p = subprocess.Popen([zarafaBackup, '-t', ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # out, err = p.communicate()
    # rc = p.returncode


#    /usr/sbin/zarafa-backup -t $_backupThreads -a -o "$_backupLocation" 2>&1 | tee "$_backupLog" 
# Mon Jan 18 00:00:06 2016: [ECThreadPool|0x6a01c700] [ notice] Backup of user KENNEDYK with 1/2414 items in 17/17 folders, written 173 KB
