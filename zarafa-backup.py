#!/usr/bin/env python
"""
Script used to backup Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, os, subprocess, sys, datetime, fnmatch
import xml.etree.ElementTree as ElementTree

args = {}
args['output'] = "text"
args['version'] = 0.3

args['location'] = '/srv/backup/brick-level-backup'
args['log'] = ''
args['threads'] = 4

zarafaAdmin = '/usr/sbin/zarafa-admin'
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
                    type=str,
                    action='store')  
  parser.add_argument('--log',
                    required=False,
                    type=str,
                    action='store')
  parser.add_argument('-t', '--threads',
                    required=False,
                    type=int,
                    action='store')
  args.update(vars(parser.parse_args()))

  if not os.isdir(args['location']):
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

  users = [ s.strip() for s in str(out).split('\n') ]
  print users