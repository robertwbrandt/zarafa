#!/usr/bin/env python

from MAPI import *
from MAPI.Util import *
import sys, json, argparse, textwrap
import pprint

sys.path.append( os.path.realpath( os.path.join( os.path.dirname(__file__), "../../common" ) ) )
import brandt
sys.path.pop()

version = 0.3
args = {}
args['user'] = ''

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
      print "Usage: " + self.__prog + " -u \"USER\""
      print "Script used to Read WebApp Signatures of Zarafa Users.\n"
      print "Options:"
      options = []
      options.append(("-h, --help",          "Show this help message and exit"))
      options.append(("-v, --version",       "Show program's version number and exit"))
      options.append(("-u, --user USER",     "Username"))
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
  parser.add_argument('-u', '--user',
                    required=True,
                    type=str,
                    action='store')
  
  args.update(vars(parser.parse_args()))

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

    return int(cr[1]), int(cr[0])

def read_settings(username):
        settings = None 
        data = None

        PR_EC_WEBACCESS_SETTINGS_JSON = PROP_TAG(PT_STRING8, PR_EC_BASE+0x72)
        st = GetDefaultStore( OpenECSession(username, '', 'file:///var/run/zarafa') )

        try:
                settings = st.OpenProperty(PR_EC_WEBACCESS_SETTINGS_JSON, IID_IStream, 0, 0)
                data = settings.Read(40960)
        except:
                print 'User has not used WebApp yet, no settings property exists.'
        return data

if __name__ == '__main__':
        output = {}
        command_line_args()
        raw_data = read_settings(args['user'])

        if raw_data:
            data = json.loads(str(raw_data)).get('settings',{}).get('zarafa',{}).get('v1',{}).get('contexts',{}).get('mail',{}).get('signatures',{})
            if 'all' in data:
                output[args['user']] = data
            else:
                output[args['user']] = { 'all':{}, 'new_message':None, 'replyforward_message':None }

        for key in output:
            if len(output[key]['all']) == 0:
                print "No signatures found for:", key
            else:
                if len(output[key]['all']) == 1:
                    print "Email Signature for   : %s" % key
                else:
                    print "Email Signatures for  : %s" % key
                if output[key]['new_message']:
                    html = ['Text','HTML'][bool(output[key]['all'][str(output[key]['new_message'])]['isHTML'])]
                    print "           New Message: %s (%s - %s)" % ( output[key]['all'][str(output[key]['new_message'])]['name'] , html , output[key]['new_message'] )
                else:
                    print "           New Message: None"

                if output[key]['replyforward_message']:
                    html = ['Text','HTML'][bool(output[key]['all'][str(output[key]['replyforward_message'])]['isHTML'])]                    
                    print " Reply/Forward Message: %s (%s - %s)" % ( output[key]['all'][str(output[key]['replyforward_message'])]['name'] , html, output[key]['replyforward_message'] )
                else:
                    print " Reply/Forward Message: None"

                preferredWidth = getTerminalSize()[0]
                for sig in output[key]['all']:
                    prefix = " %s: " % output[key]['all'][sig]['name']
                    wrapper = textwrap.TextWrapper(initial_indent=prefix, width=preferredWidth, subsequent_indent=' '*len(prefix))
                    print wrapper.fill(output[key]['all'][sig]['content'])

                pprint.pprint(raw_data)



            print "\n"
