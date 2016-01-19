#!/usr/bin/env python
"""
Script used to backup Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, os, subprocess, datetime
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

  for line in out.split('\n'):
    tmp = line.split('[')
    if len(tmp) == 2:
      tmp = [ str(s).strip() for s in tmp[2].split(']') ]
      print tmp

    

  exit()



# [info   ] Starting backup of user brandtb
# [info   ] Starting incremental backup for user brandtb
# [info   ] Starting full backup for user BRADYJN
