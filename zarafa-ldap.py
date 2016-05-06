#!/usr/bin/env python
"""
Python utility to monitor when LDAP attributes change and issue --sync command to Zarafa
"""
import argparse, textwrap, fnmatch, datetime, urllib, json
import xml.etree.cElementTree as ElementTree
import subprocess

# Import Brandt Common Utilities
import sys, os
sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "/opt/brandt/common" ) ) )
import brandt
sys.path.pop()

args = {}

version = 0.3
encoding = 'utf-8'

zarafaFiles   = {'server.cfg': '/etc/zarafa/server.cfg',
                 'ldap.propmap.cfg': '/etc/zarafa/ldap.propmap.cfg',
                 'ldap.cfg': '/etc/zarafa/ldap.active-directory.cfg'}
zarafaLDAP    = {}
zarafaAttrs   = set(["objectclass"])
zarafaFilter  = ""
zarafaLDAPURL = ""
zarafaCacheFile = "/tmp/zarafa.ldap.cache"

dominoLDAPURL = "ldap://domino.i.opw.ie/?objectclass,mail,member, mailaddress?sub?(|(objectClass=dominoPerson)(objectClass=dominoGroup))"
dominoCacheFile = "/tmp/domino.ldap.cache"


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
      options.append(("-h, --help",              "Show this help message and exit"))
      options.append(("-v, --version",           "Show program's version number and exit"))
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
  args.update(vars(parser.parse_args()))

def get_zarafa_ldap():
  global zarafaFiles, zarafaLDAP, zarafaAttrs, zarafaFilter

  f = open(zarafaFiles['server.cfg'], 'r')
  out = f.read()
  f.close()
  for line in out.split('\n'):
    if str(line)[:18].lower() == "user_plugin_config":
      line = line.split("=",1)
      if len(line) == 2: 
        zarafaFiles['ldap.cfg'] = str(line[1]).strip()
        break

  f = open(zarafaFiles['ldap.cfg'], 'r')
  out = f.read()
  f.close()
  for line in out.split('\n'):
    if line and str(line)[0] not in ['#',';']:
      line = line.split("=",1)
      if len(line) == 2 and line[1].strip(): 
        zarafaLDAP[str(line[0]).strip().lower()] = str(line[1]).strip()

  f = open(zarafaFiles['ldap.propmap.cfg'], 'r')
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

  for key in zarafaLDAP.keys():
    if key[-6:] == 'filter':
      zarafaFilter += zarafaLDAP[key]
  zarafaFilter = "(|" + zarafaFilter +")"

  zarafaLDAPURL = zarafaLDAP.get('ldap_uri','').split(" ")[0]
  if not zarafaLDAPURL:
    zarafaLDAPURL = zarafaLDAP.get('ldap_protocol','ldap') + '://' + zarafaLDAP.get('ldap_host','')
    if zarafaLDAP.has_key('ldap_port'): zarafaLDAPURL += ':' + zarafaLDAP['ldap_port']
  if zarafaLDAPURL[-1] != "/": zarafaLDAPURL += '/'
  zarafaLDAPURL += urllib.quote(zarafaLDAP['ldap_search_base'])
  zarafaLDAPURL += "?" + urllib.quote(",".join(sorted(zarafaAttrs)))
  zarafaLDAPURL += "?sub"
  zarafaLDAPURL += "?" + zarafaFilter
  if zarafaLDAP.has_key('ldap_bind_user'): zarafaLDAPURL += "?bindname=" + urllib.quote(zarafaLDAP['ldap_bind_user']) + ",X-BINDPW=" + urllib.quote(zarafaLDAP['ldap_bind_passwd'])

  results = brandt.LDAPSearch(zarafaLDAPURL).results
  return results

def get_domino_ldap():
  global dominoLDAPURL
  results = brandt.LDAPSearch(dominoLDAPURL).results
  return results

def write_domino_ldap(results):
  global dominoCacheFile
  json.dump(results, 
            open(dominoCacheFile,'w'),
            sort_keys=True,
            indent=2)

def read_domino_ldap():
  global dominoCacheFile  
  return json.load(open(dominoCacheFile,'r'))


# Start program
if __name__ == "__main__":
  command_line_args()  

  # zarafaResults = get_zarafa_ldap()
  dominoResults = get_domino_ldap()
  write_domino_ldap(dominoResults)
  dominoResults2 = read_domino_ldap()
  print dominoResults2



