#!/usr/bin/env python
"""
Python utility to monitor when LDAP attributes change and issue --sync command to Zarafa
"""
import argparse, textwrap, fnmatch, datetime, urllib, json, re
import xml.etree.cElementTree as ElementTree
import subprocess

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "/opt/brandt/common" ) ) )
import brandt
sys.path.pop()

args = {}
args['config'] = '/etc/zarafa/server.cfg'
args['force'] = False
args['web'] = False
args['minObjects'] = 800

version = 0.4
encoding = 'utf-8'

zarafaLDAP       = {}
zarafaFilter     = ""
zarafaLDAPURL    = ""
zarafaAttrAdd    = set(["objectclass","samaccountname"])
zarafaAttrIgnore = set(["usnchanged","objectguid","grouptype","unicodepwd"])
zarafaCacheFile  = "/tmp/zarafa.ldap.cache"

dominoLDAPURI = "ldap://domino.i.opw.ie/?objectclass,mail,member,mailaddress?sub?(|(objectClass=dominoPerson)(objectClass=dominoGroup))"
dominoCacheFile  = "/tmp/domino.ldap.cache"

emailCacheFile   = "/tmp/email.ldap.cache"

postfixBCC = "/etc/postfix/bcc"
postfixVTrans = "/etc/postfix/vtransport"

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
      print "Usage: " + self.__prog + " [options]"
      print "Python utility to monitor when LDAP attributes change and issue --sync command to Zarafa.\n"
      print "Options:"
      options = []
      options.append(("-h, --help",          "Show this help message and exit"))
      options.append(("-v, --version",       "Show program's version number and exit"))
      options.append(("-c, --config CONFIG", "Zarafa Configuration file (Default: " + args['config'] + ")"))
      options.append(("-f, --force",         "Force sync"))
      options.append(("-w, --web",           "Web XML only"))
      length = max( [ len(option[0]) for option in options ] )
      for option in options:
        description = textwrap.wrap(option[1], (self.__row - length - 5))
        print "  " + option[0].ljust(length) + "   " + description[0]
      for n in range(1,len(description)): print " " * (length + 5) + description[n]
    exit(self.__exit)
def command_line_args():
  global args, version
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('-v', '--version', action=customUsageVersion, version=version, max=80)
  parser.add_argument('-h', '--help', action=customUsageVersion)
  parser.add_argument('-c', '--config',
                      required=False,
                      default=args['config'],
                      type=str,
                      help="Zarafa Configuration file")
  parser.add_argument('-f', '--force',
                      required=False,
                      default=args['force'],
                      action="store_true",
                      help="Force sync")
  parser.add_argument('-w', '--web',
                      required=False,
                      default=args['web'],
                      action="store_true",
                      help="Web XML only")  
  args.update(vars(parser.parse_args()))


def get_zarafa_LDAPURI():
  global args, zarafaAttrIgnore
  ldapConfig  = ""
  ldapPropMap = ""
  zarafaAttrs = set(["objectclass"])
  zarafaFilter = ""

  f = open(args['config'], 'r')
  out = f.read()
  f.close()
  for line in out.split('\n'):
    if str(line)[:18].lower() == "user_plugin_config":
      line = line.split("=",1)
      if len(line) == 2: 
        ldapConfig = str(line[1]).strip()
        break

  f = open(ldapConfig, 'r')
  out = f.read()
  f.close()
  for line in out.split('\n'):
    if str(line)[:9].lower() == "!propmap ":
      ldapPropMap = str(line.split(" ",1)[1]).strip()
      continue

    if line and str(line)[0] not in ['#',';']:
      line = line.split("=",1)
      if len(line) == 2 and line[1].strip(): 
        zarafaLDAP[str(line[0]).strip().lower()] = str(line[1]).strip()

  f = open(ldapPropMap, 'r')
  out = f.read()
  f.close()
  for line in out.split('\n'):
    if line and str(line)[0] not in ['#',';']:
      line = line.split("=",1)
      if len(line) == 2 and line[1].strip(): 
        zarafaAttrs.add(str(line[1]).strip().lower())

  for key in zarafaLDAP.keys():
    if key[-9:] == 'attribute':
      zarafaAttrs.add(zarafaLDAP[key].lower())
  zarafaAttrs -= zarafaAttrIgnore

  for key in zarafaLDAP.keys():
    if key[-6:] == 'filter':
      zarafaFilter += zarafaLDAP[key]
  zarafaFilter = "(|" + zarafaFilter +")"

  zarafaLDAPURI = zarafaLDAP.get('ldap_uri','').split(" ")[0]
  if not zarafaLDAPURI:
    zarafaLDAPURI = zarafaLDAP.get('ldap_protocol','ldap') + '://' + zarafaLDAP.get('ldap_host','')
    if zarafaLDAP.has_key('ldap_port'): zarafaLDAPURI += ':' + zarafaLDAP['ldap_port']
  if zarafaLDAPURI[-1] != "/": zarafaLDAPURI += '/'
  zarafaLDAPURI += urllib.quote(zarafaLDAP['ldap_search_base'])
  zarafaLDAPURI += "?" + urllib.quote(",".join(sorted(zarafaAttrs)))
  zarafaLDAPURI += "?sub"
  zarafaLDAPURI += "?" + zarafaFilter
  if zarafaLDAP.has_key('ldap_bind_user'): zarafaLDAPURI += "?bindname=" + urllib.quote(zarafaLDAP['ldap_bind_user']) + ",X-BINDPW=" + urllib.quote(zarafaLDAP.get('ldap_bind_passwd',""))

  return zarafaLDAPURI

def get_ldap(LDAPURI):
  # try:
    return brandt.LDAPSearch(LDAPURI).resultsDict(functDN=lambda dn: brandt.strXML(brandt.formatDN(dn)),
                                                  functAttr=lambda a: brandt.strXML(str(a).lower()), 
                                                  functValue=lambda *v:brandt.strXML(brandt.formatDN(v[-1])))
  # except:
  #   return {}

def write_cache_file(filename, data):
  json.dump(data, open(filename, 'w'), sort_keys=True, indent=2)

def read_cache_file(filename):
  try:
    return json.load(open(filename,'r'))
  except:
    return {}

def cmpDict(dict1, dict2):
  global args,output

  try:  
    if set(dict1.keys()) != set(dict2.keys()): 
      output += "Changes Found:\n"
      if bool(set(dict1.keys()) - set(dict2.keys())):
        output += "New DNs: " + ", ".join(list(set(dict1.keys()))) + "\n"
      if bool(set(dict2.keys()) - set(dict1.keys())):
        output += "Removed DNs: " + ", ".join(list(set(dict2.keys()))) + "\n"
      return False
    for dn in dict1.keys():
      if sorted(dict1[dn].keys()) != sorted(dict2[dn].keys()):
        output += "Changes Found:\n"
        if bool(set(dict1[dn].keys()) - set(dict2[dn].keys())):
          output += "New Attribute for (" + str(dn) + "): " + ", ".join(list(set(dict1[dn].keys()))) + "\n"
        if bool(set(dict2[dn].keys()) - set(dict1[dn].keys())):
          output += "Removed Attribute for (" + str(dn) + "): " + ", ".join(list(set(dict2[dn].keys()))) + "\n"
        return False
      for attr in dict1[dn].keys():
        if sorted(dict1[dn][attr]) != sorted(dict2[dn][attr]):
          output += "Changes Found:\n"
          output += "Value of Attribute(" + str(attr) + ") for (" + str(dn) + "):\n"
          output += "Old: " + ", ".join(sorted(dict2[dn][attr])) + "\n"
          output += "New: " + ", ".join(sorted(dict1[dn][attr])) + "\n"
          return False
  except:
    return False
  return True

def get_data():
  global args, output

  zarafaChanged = False
  combinedEmails = read_cache_file(emailCacheFile)
  date = None
  if combinedEmails: date = datetime.datetime.fromtimestamp(os.stat(emailCacheFile).st_mtime)

  if not combinedEmails or not args['web']:
    date = datetime.datetime.now()
    zarafaURI = get_zarafa_LDAPURI()
    zarafaLive = get_ldap(zarafaURI)
    if len(zarafaLive) < args['minObjects']:
      tmp = "Unable to get reliable Zarafa Download. Only " + str(len(zarafaLive)) + " objects."
      tmp += '\n' + str(zarafaURI)
      raise IOError, tmp
    zarafaCache = read_cache_file(zarafaCacheFile)
    output += "Checking Zarafa entries\n"
    if not cmpDict(zarafaLive, zarafaCache):
      output += "Zarafa entries have changed\n"
      write_cache_file(zarafaCacheFile,zarafaLive)
      zarafaChanged = True

    dominoLive = get_ldap(dominoLDAPURI)
    if len(dominoLive) < args['minObjects']:
      tmp = "Unable to get reliable Domino Download. Only " + str(len(dominoLive)) + " objects."
      tmp += '\n' + str(dominoLDAPURI)
      raise IOError, tmp
    write_cache_file(dominoCacheFile,dominoLive)

    combinedEmails = {}
    for account in zarafaLive.keys():
      for mail in zarafaLive[account].get('mail',[]) + zarafaLive[account].get('othermailbox',[]):
        objectclass = set([ str(x).lower() for x in zarafaLive[account].get('objectclass',[]) ])
        combinedEmails[mail] = {'zarafa':True, 
                                'domino':False, 
                                'forward':False, 
                                'type':'', 
                                'username':str(zarafaLive[account].get('samaccountname',[''])[0])}
        if bool(set(["group","dominogroup","groupofnames"]) & objectclass):
          combinedEmails[mail]['type'] = "Group"
        elif bool(set(["person","user","dominoperson","inetorgperson","organizationalperson"]) & objectclass):
          combinedEmails[mail]['type'] = "User"
        else:
          combinedEmails[mail]['type'] = ",".join(sorted(objectclass))

    for account in dominoLive.keys():
      for mail in dominoLive[account].get('mail',[]):
        objectclass = set([ str(x).lower() for x in dominoLive[account].get('objectclass',[]) ])
        if not combinedEmails.has_key(mail):
          combinedEmails[mail] = {'zarafa':False, 
                                  'domino':True, 
                                  'forward':False, 
                                  'type':'', 
                                  'username':''}
        if bool(set(["group","dominogroup","groupofnames"]) & objectclass):
          combinedEmails[mail]['type'] = "Group"
        elif bool(set(["person","user","dominoperson","inetorgperson","organizationalperson"]) & objectclass):
          combinedEmails[mail]['type'] = "User"
        else:
          combinedEmails[mail]['type'] = ",".join(sorted(objectclass))
        combinedEmails[mail]['domino'] = True
        combinedEmails[mail]['forward'] = dominoLive[account].has_key('mailaddress')


    write_cache_file(emailCacheFile,combinedEmails)

  return (zarafaChanged, date, combinedEmails)

# Start program
if __name__ == "__main__":
  try:
    output = ""
    error = ""
    exitcode = 0    
    xmldata = None

    command_line_args()  
    zarafaChanged, date, emails = get_data()

    if args['web']:
      xmldata = ElementTree.Element('emails', **{'date': brandt.strXML(datetime.datetime.strftime(date,'%Y-%m-%d %H:%M:%S'))})
      for email in sorted(emails.keys()):
        ElementTree.SubElement(xmldata, 'email', **{'mail': brandt.strXML(email), 
                                        'zarafa': brandt.strXML(emails[email]['zarafa']), 
                                        'domino': brandt.strXML(emails[email]['domino']), 
                                        'forward': brandt.strXML(emails[email]['forward']),
                                        'username': brandt.strXML(emails[email]['username']),
                                        'type': brandt.strXML(emails[email]['type'])})
    else:
      if zarafaChanged or args['force']:
        output += brandt.syslog("Changes detected: Running Zarafa Sync\n", options=['pid'])
        command = '/usr/sbin/zarafa-admin --sync'
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err: raise IOError(err)
        output += out + "\n"

      reloadPostfix = False

      f = open(postfixBCC, 'r')
      out = f.read().split('\n')
      f.close()
      oldFile = set([])
      for line in out:
        if line and not line[0] in ["#",";"]:
          oldFile.add(line.split()[0].lower())
      newFile = set([ k for k in emails.keys() if (emails[k]['type'] == "User") and emails[k]['zarafa'] and ( emails[k]['domino'] == emails[k]['forward'] ) ])
      output += "Checking Postfix BCC entries\n"
      if len(oldFile ^ newFile) or args['force']:
        reloadPostfix = True
        tmp = "Changes detected: Rebuilding Postfix BCC file for Mailmeter\n"
        tmp += "Removed BCC emails:" + ", ".join(sorted(oldFile - newFile)) + "\n"
        tmp += "Added BCC emails:" + ", ".join(sorted(newFile - oldFile)) + "\n"
        output += brandt.syslog(tmp, options=['pid'])

        tmp = "# /etc/postfix/bcc - OPW Postfix BCC Mapping for Zarafa Only users\n"
        for mail in sorted(newFile):
          tmp += mail + "\tarchive@mailmeter.opw.ie\n"
        f = open(postfixBCC, 'w')
        f.write(tmp)
        f.close()

      f = open(postfixVTrans, 'r')
      out = f.read().split('\n')
      f.close()
      oldFile = {}
      for line in out:
        if line and not line[0] in ["#",";"]:
          tmp = str(line).lower().split()
          oldFile[tmp[0]] = sorted([ x.strip() for x in tmp[1:] if x.strip() ])
      newFile = {}
      for mail in sorted(emails.keys()):
        if emails[mail]['domino'] and not emails[mail]['forward']:
          newFile[mail] = [ re.sub('@opw.ie$','@dublinnotes.opw.ie',mail) ]
          if emails[mail]['zarafa']: newFile[mail].append(mail)
          newFile[mail] = sorted(newFile[mail])
      output += "Checking Postfix vTransport entries\n"          
      same = bool( set(oldFile.keys()) == set(newFile.keys()) )
      if same:
        for mail in oldFile.keys():
          same = bool( oldFile[mail] == newFile[mail] )
          if not same: break
      if not same or args['force']:
        reloadPostfix = True
        tmp = "Changes detected: Rebuilding Postfix vTransport file for Smarthost\n"
        tmp += "Removed vTransport emails:" + ", ".join(sorted(set(oldFile.keys()) - set(newFile.keys()))) + "\n"
        tmp += "Added vTransport emails:" + ", ".join(sorted(set(newFile.keys()) - set(oldFile.keys()))) + "\n"
        output += brandt.syslog(tmp, options=['pid'])

        tmp = "# /etc/postfix/vtransport - OPW Postfix virtual transport for Lotus Notes\n"
        tmp += "# this file configures virtual transport for Lotus Notes only accounts (users & groups accounts)\n"
        tmp += "# and for Zarafa & Lotus notes accounts (users & groups accounts, no aliases exist)\n"
        for mail in sorted(newFile.keys()):
          tmp += mail + "\t" + "\t".join(newFile[mail]) + "\n"
        f = open(postfixVTrans, 'w')
        f.write(tmp)
        f.close()

      if reloadPostfix or args['force']:
        output += brandt.syslog("Rebuilding Postmaps\n", options=['pid'])      
        command = '/usr/sbin/postmap ' + postfixBCC 
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err: raise IOError(err)
        output += out + "\n"

        command = '/usr/sbin/postmap ' + postfixVTrans 
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err: raise IOError(err)
        output += out + "\n"

        output += brandt.syslog("Reloading Postfix\n", options=['pid'])      
        command = 'service postfix reload'
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err: raise IOError(err)
        output += out + "\n"

  except SystemExit as err:
    pass
  except Exception as err:
    try:
      exitcode = int(err[0])
      errmsg = str(" ".join(err[1:]))
    except:
      exitcode = -1
      errmsg = str(err)

    if args['web']: 
      error = "(" + str(exitcode) + ") " + str(errmsg) + "\nCommand: " + " ".join(sys.argv)
    else:
      xmldata = ElementTree.Element('error', code=brandt.strXML(exitcode), 
                                             msg=brandt.strXML(errmsg), 
                                             cmd=brandt.strXML(" ".join(sys.argv)))
  finally:
    if not args['web']: 
      if output: print str(output)
      if error:  sys.stderr.write( str(error) + "\n" )
    else:    
      xml = ElementTree.Element('zarafaadmin')
      xml.append(xmldata)
      print '<?xml version="1.0" encoding="' + encoding + '"?>\n' + ElementTree.tostring(xml, encoding=encoding, method="xml")
    sys.exit(exitcode)

