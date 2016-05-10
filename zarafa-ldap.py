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
args['config'] = '/etc/zarafa/server.cfg'
version = 0.3
encoding = 'utf-8'

zarafaLDAP    = {}
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
      options.append(("-h, --help",         "Show this help message and exit"))
      options.append(("-v, --version",      "Show program's version number and exit"))
      options.append(("-c, --config",       "Zarafa Configuration file"))
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
                      help="Zarafa Configuration file.")  
  args.update(vars(parser.parse_args()))


def get_zarafa_LDAPURI():
  global args
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
  return brandt.LDAPSearch(LDAPURI).results

def write_cache_file(filename, results):
  json.dump(results, 
            open(filename,'w'),
            sort_keys=True,
            indent=2)

def read_cache_file(filename):
  return json.load(open(filename,'r'))


# Start program
if __name__ == "__main__":
  command_line_args()  

  zarafaLDAPURI = get_zarafa_LDAPURI()

  print zarafaLDAPURI

  # dominoResults = get_domino_ldap()
  # write_domino_ldap(dominoResults)
  # dominoResults2 = read_domino_ldap()
  # print dominoResults2



