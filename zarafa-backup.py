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


  errors = 0
  f = open(args['log'], 'a')
  for user in sorted([ str(s.strip().split('\t')[0]).lower() for s in str(out).split('\n')[4:] if s ])[:3]:
    dateStr = str(datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y:')).ljust(26)

    logStr = dateStr + str('[zarafa-backup] [ notice]').rjust(35) + ' Starting backup of user ' + user
    f.write(logStr + '\n')
    if args['output'] == 'text':
      print logStr

    p = subprocess.Popen([zarafaBackup, '-v', '-t', str(args[threads]), '-o', args['location'] , '-u', user], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    rc = p.returncode
  
    f.write(out + '\n')
    if args['output'] == 'text':
      print logStr

    if err or rc:
      f.write(err + '\n')
      errors += 1
      if args['output'] == 'text':
        print logStr

  dateStr = str(datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y:')).ljust(26)
  if errors == 0:
    logStr = dateStr + str('[zarafa-backup] [ notice]').rjust(35) + ' Zarafa Backup has completed with no errors.'
  else:
    logStr = dateStr + str('[zarafa-backup] [  fatal]').rjust(35) + ' Zarafa Backup has completed with ' + str(errors) + " errors."
  f.write(logStr + '\n')
  f.close()

  if args['output'] == 'text':
    print logStr

  if errors:
    exit(errors)

  exit()
