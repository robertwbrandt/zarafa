#!/usr/bin/env python
"""
Script used to restore Zarafa Mailboxes using brick-level-backup commands.
"""
import argparse, os, subprocess, sys, datetime, fnmatch
import xml.etree.ElementTree as ElementTree




msgReadScript = '/usr/share/zarafa-backup/readable-index.pl'
msgRestoreScript = '/usr/sbin/zarafa-restore'
msgBackupLocation = '/srv/backup/brick-level-backup/'

msgTypeValues = ['folder', 'message']
msgItemValues = {}
# IPF.Appointment
# IPF.Configuration
# IPF.Contact
# IPF.Journal
# IPF.Note
# IPF.Note.OutlookHomepage
# IPF.StickyNote
# IPF.Task
# IPM.Appointment
# IPM.Note
# IPM.Note.StorageQuotaWarning
# IPM.Schedule.Meeting.Canceled
# IPM.Schedule.Meeting.Request
# IPM.Schedule.Meeting.Resp.Neg
# IPM.Schedule.Meeting.Resp.Pos

def sortDictbyDate(d):
  return sorted(d.keys(), key=lambda x: d[x]['date'])


def find(username, msgID = None, msgType = None, msgDateStart = None, msgDateEnd = None, msgItem = None, msgExtra = None, msgSubject = None):
  
  username = str(username).lower() + '.index.zbk'
  if msgID: msgID   = str(msgID).lower()
  if msgType: msgType   = str(msgType).lower()
  if msgItem: msgItem   = str(msgItem).lower()
  if msgExtra: msgExtra = str(msgExtra).lower()
  if msgSubject: msgSubject   = str(msgSubject).lower()

  if msgType not in msgTypeValues: msgType = None
  if msgItem not in msgItemValues.keys(): msgItem = None
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
  print "Found index file", filename


  p = subprocess.Popen([msgReadScript, filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = p.returncode

  if rc > 0 or err:
    exit("Error: " + str('\n'.join([out,err])).strip() )

  results = {}
  for line in str(out).split('\n')[1:]:
    if line:
      tmp = str(line).split('\t') + [None,None,None,None,None]
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

  restoreCMD = [msgRestoreScript, '-v', '-r', '-u', username, '-f', os.path.join(msgBackupLocation, username)]
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





# tmp = find("SYDENHAJ", msgDateStart="2-12-2005")

# for k in sortDictbyDate(tmp):
#   print k, tmp[k]['msgUser'], tmp[k]['msgType'], tmp[k]['msgDate'], tmp[k]['msgItem'], tmp[k]['msgExtra'], tmp[k]['msgSubject']


restore('SYDENHAJ', '2CA26800', msgDateStart = "1-12-2015", msgDateEnd = "7-12-2015")

