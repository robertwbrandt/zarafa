#!/usr/bin/env python
"""
Script used to restore Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, textwrap
import subprocess
import datetime, fnmatch
import xml.etree.ElementTree as ElementTree

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "../common" ) ) )
import brandt
sys.path.pop()

version = 0.3
args = {}
args['output'] = "text"
args['location'] = '/srv/backup/brick-level-backup'
args['cmd'] = ''
args['user'] = ''
args['id'] = ''
args['type'] = ''
args['start'] = ''
args['end'] = ''
args['item'] = ''
args['extra'] = ''
args['subject'] = ''

zarafaScript = '/usr/share/zarafa-backup/readable-index.pl'
zarafaRestore = '/usr/sbin/zarafa-restore'
msgBackupLocation = '/srv/backup/brick-level-backup/'
encoding = "utf-8"

msgTypeValues = ['folder', 'message']
msgItemValues = ['appointment','configuration','contact','distlist','documentlibrary','journal','note','post','recall','schedule','stickynote','task', 'other']

class customUsageVersion(argparse.Action):
  def __init__(self, option_strings, dest, **kwargs):
    self.__version = str(kwargs.get('version', ''))
    self.__prog = str(kwargs.get('prog', os.path.basename(__file__)))
    self.__row = min(int(kwargs.get('max', 80)), brandt.getTerminalSize()[0])
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
      print "Usage: " + self.__prog + " [options] {find | restore} USER"
      print "Script used to restore items to Zarafa Mailboxes via brick-level-backup.\n"
      print "Options:"
      options = []
      options.append(("-h, --help",              "Show this help message and exit"))
      options.append(("-v, --version",           "Show program's version number and exit"))
      options.append(("-o, --output OUTPUT",     "Type of output {text | xml}"))
      options.append(("-l, --location LOCATION", "Backup location"))
      options.append(("-t, --type TYPE",         "Type of msg {" + " | ".join(msgTypeValues) + "}"))
      options.append(("-i, --item ITEM",         "Item ID {" + " | ".join(msgItemValues) + "}"))
      options.append(("-e, --extra EXTRA",       "Msg extra info"))
      options.append(("-s, --subject SUBJECT",   "Msg subject"))
      options.append(("    --id MSGID",          "Msg ID"))
      options.append(("    --start START",       "Start Date (in format DD-MM-YYYY)"))
      options.append(("    --end END",           "End Date (in format DD-MM-YYYY)"))
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
  parser.add_argument('-o', '--output',
                    required=False,
                    default=args['output'],
                    choices=['text', 'xml'])
  parser.add_argument('-l', '--location',
                    required=False,
                    default=args['location'],
                    type=str,
                    action='store')
  parser.add_argument('-t', '--type',
                    choices=msgTypeValues,
                    required=False,
                    type=str,
                    action='store')    
  parser.add_argument('-i', '--item',
                    required=False,
                    choices=msgItemValues,
                    type=str,
                    action='store')  
  parser.add_argument('-e', '--extra',
                    required=False,
                    type=str,
                    action='store')  
  parser.add_argument('-s', '--subject',
                    required=False,
                    type=str,
                    action='store') 
  parser.add_argument('--id',
                    required=False,
                    type=str,
                    action='store')   
  parser.add_argument('--start',
                    required=False,
                    type=str,
                    action='store')  
  parser.add_argument('--end',
                    required=False,
                    type=str,
                    action='store')
  parser.add_argument('cmd',
                    choices=['find', 'restore'],
                    type=str,
                    action='store')
  parser.add_argument('user',
                    type=str,
                    action='store')    
  args.update(vars(parser.parse_args()))

  if not os.path.isdir(str(args['location'])):
    exit('The path specified (' + str(args['location']) + ') does not exist.')
  if args['start']:
    tmp = args['start'].split('-')
    if not (len(tmp) == 3 and int(tmp[0]) in range(1,32) and int(tmp[1]) in range(1,13) and int(tmp[1]) > 0):
      exit('The start date must be in the format DD-MM-YYYY')
  if args['end']:
    tmp = args['end'].split('-')
    if not (len(tmp) == 3 and int(tmp[0]) in range(1,32) and int(tmp[1]) in range(1,13) and int(tmp[1]) > 0):
      exit('The end date must be in the format DD-MM-YYYY')



def find(username, msgID = None, msgType = None, msgDateStart = None, msgDateEnd = None, msgItem = None, msgExtra = None, msgSubject = None):
  
  username = str(username).lower() + '.index.zbk'
  if msgID: msgID   = str(msgID).lower()
  if msgType: msgType   = str(msgType).lower()
  if msgItem: msgItem   = str(msgItem).lower()
  if msgExtra: msgExtra = str(msgExtra).lower()
  if msgSubject: msgSubject   = str(msgSubject).lower()

  if msgType not in msgTypeValues: msgType = None
  if msgItem not in msgItemValues: msgItem = None
  if msgDateStart:
    msgDateStart = datetime.datetime.strptime(msgDateStart, "%d-%m-%Y")
  if msgDateEnd:
    msgDateEnd = datetime.datetime.strptime(msgDateEnd, "%d-%m-%Y") 
  if msgDateStart and not msgDateEnd:
    msgDateEnd = datetime.datetime.now()
  if msgDateEnd and not msgDateStart:
    msgDateStart = datetime.datetime.strptime("1-1-0001", "%d-%m-%Y")

  for (dirpath, dirnames, filenames) in os.walk(msgBackupLocation):
    break
  filename = [ f for f in filenames if str(f).lower() == username ]
  if len(filename) > 1: 
    exit("The search returned more than one index file!")
  elif len(filename) < 1: 
    exit("The search didn't return an index file!")
  else:
    username = str(filename[0]).split('.',1)[0]
    filename = os.path.join(msgBackupLocation, filename[0])
  #print "Found index file", filename

  p = subprocess.Popen([zarafaScript, filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = p.returncode

  if rc > 0 or err:
    exit("Error: " + str('\n'.join([out,err])).strip() )

  results = {}
  for line in str(out).split('\n')[1:]:
    if line:
      tmp = str(line).split('\t') + [None,None,None,None,None]
      try:
        tmp[3] = (str(tmp[3]).split('.')[1]).lower()
      except:
        tmp[3] = "other"
      add = True
      tmpDate = None
      strDate = 0
      if msgID:
        add = (str(tmp[0]).lower() == msgID)
      if msgType:
        add = (tmp[1] == msgType)        
      if tmp[2]:
        tmpDate = datetime.datetime.strptime(tmp[2], "%a %b %d %H:%M:%S %Y")
        strDate = tmpDate.strftime("%Y%m%d%H%M%S")
      if msgDateStart and tmpDate:
        add = (msgDateStart <= tmpDate <= msgDateEnd)
      if msgItem:
        add = (tmp[3] == msgItem)
      if msgExtra and tmp[4]:
        add = fnmatch.fnmatch(str(tmp[4]).lower(), msgExtra)
      if msgSubject and tmp[5]:
        add = fnmatch.fnmatch(str(tmp[5]).lower(), msgSubject)
      if add:
        results[tmp[0]] = {'msgUser':username, 'msgType':tmp[1], 'msgDate':tmp[2], 'date':strDate, 'msgItem':tmp[3], 'msgExtra':tmp[4], 'msgSubject':tmp[5]}
  return results




def restore(username, msgID, msgDateStart = None, msgDateEnd = None):
  if msgDateStart and not msgDateEnd:
    msgDateEnd = datetime.datetime.now().strftime("%d-%m-%Y")
  if msgDateEnd and not msgDateStart:
    msgDateStart = "1-1-0001"

  restoreCMD = [zarafaRestore, '-v', '-r', '-u', username, '-f', os.path.join(msgBackupLocation, username)]
  if msgDateStart:
    restoreCMD += ['-b', msgDateStart, '-a', msgDateEnd]
  restoreCMD.append(msgID)

  return 0

  # print "Restoring Message", msgID, " from ", username, " mail store."
  # p = subprocess.Popen(restoreCMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  # out, err = p.communicate()
  # rc = p.returncode
  # print out
  # if err: print err
  # return rc





# Start program
if __name__ == "__main__":
  command_line_args()

  results = find("brandtb", msgDateStart="19-1-2016")

  if args['cmd'] == 'find':
    if args['output'] == 'text':
      length={}
      length['msgUser'] = max( len(args['user']), 8)      
      length['msgType'] = max( [ len(m['msgType']) for m in results.values() ] )
      length['msgDate'] = max( [ len(m['msgDate']) for m in results.values() ] )
      length['msgItem'] = max( [ len(m['msgItem']) for m in results.values() ] )
      length['msgExtra'] = max( [ len(m['msgExtra']) for m in results.values() ] )

      print "Msg ID".center(8), "Username".center(length['msgUser']), "Type".center(length['msgType']), "Date".center(length['msgDate']), "Item".center(length['msgItem']), "Extra".center(length['msgExtra']), "     Subject"
      for k in brandt.sortDictbyField(results,'date'):
        print k, results[k]['msgUser'].ljust(length['msgUser']), results[k]['msgType'].ljust(length['msgType']), results[k]['msgDate'].center(length['msgDate']), results[k]['msgItem'].title().ljust(length['msgItem']), results[k]['msgExtra'].ljust(length['msgExtra']), results[k]['msgSubject']
    else:
      print args

      attrib=args.copy()
      del attrib['help'], attrib['version'], attrib['cmd'], attrib['output'], attrib['location'] 
      print attrib
      for k in attrib.keys():
        if not attrib[k]: del attrib[k]
      print attrib


      # xml = ElementTree.Element('zarafa-restore')
      # m = ElementTree.SubElement(xml, 'message', attrib={'name':deamon})
      # t = ElementTree.SubElement(d, show, attrib={'command':command, 'returncode':str(self.__deamons[deamon][show]["returncode"]), 'name':self.__deamons[deamon][show]['deamon']})
      # o = ElementTree.SubElement(t, 'output')
      # o.text = self.__deamons[deamon][show]["output"]
      # e = ElementTree.SubElement(t, 'error')
      # e.text = self.__deamons[deamon][show]["error"]
      # output = '<?xml version="1.0" encoding="' + self.__encoding + '"?>\n' + ElementTree.tostring(xml, encoding=self.__encoding, method="xml")





  else:
    print "Restore"


  #restore('SYDENHAJ', '2CA26800', msgDateStart = "1-12-2015", msgDateEnd = "7-12-2015")




