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
args['file'] = 'STDIN'
args['name'] = ''
args['user'] = ''
args['text'] = False
args['new'] = False
args['reply'] = False

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
      options.append(("-h, --help",          "Show this help message and exit"))
      options.append(("-v, --version",       "Show program's version number and exit"))
      options.append(("-f, --file FILENAME", "File containing the signature (Default: STDIN)"))
      options.append(("-n, --name NAME",     "Name of the Signature"))
      options.append(("-u, --user USER",     "Username"))
      options.append(("-t, --text",          "Text only signature" ))
      options.append(("    --new",           "Use as default signature for New Messages"))
      options.append(("    --reply",         "Use as default signature for forward or Reply Messages"))
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
  parser.add_argument('-f', '--file',
                    required=True,
                    default=args['file'],
                    type=str,
                    action='store')
  parser.add_argument('-n', '--name',
                    required=True,
                    type=str,
                    action='store')
  parser.add_argument('-u', '--user',
                    required=True,
                    type=str,
                    action='store')  
  parser.add_argument('-t', '--text',
                    required=False,
                    action='store_false')  
  parser.add_argument('--new',
                    required=False,
                    action='store_false')  
  parser.add_argument('--reply',
                    required=False,
                    action='store_false')    
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



def write_settings(username):

        PR_EC_WEBACCESS_SETTINGS_JSON = PROP_TAG(PT_STRING8, PR_EC_BASE+0x72)
        st = GetDefaultStore( OpenECSession(username, '', 'file:///var/run/zarafa') )


        settings = st.OpenProperty(PR_EC_WEBACCESS_SETTINGS_JSON, IID_IStream, 0, MAPI_MODIFY|MAPI_CREATE)
        settings.SetSize(0)
        settings.Seek(0, STREAM_SEEK_END)

        defaultSettings='{"settings":{"zarafa":{"v1":{"main":{"language":"en_GB","default_context":"mail","start_working_hour":540,"end_working_hour":1020,"week_start":1,"show_welcome":false},"contexts":{"mail":[],"calendar":{"default_zoom_level":30,"datepicker_show_busy":true}},"state":{"models":{"note":{"current_data_mode":0}},"contexts":{"mail":{"current_view":0,"current_view_mode":1}}}}}}}'

        newSettings = ''
        try:
                newSettings = sys.stdin.read()
        except:
                newSettings = defaultSettings
        if not newSettings:
                newSettings = defaultSettings

        ## Basic set of, leaves welcome screen:
        # writesettings = settings.Write('{"settings":{"zarafa":{"v1":{"main":{"language":"nl_NL.UTF-8"},"contexts":{"mail":[]}}}}}')

        ## Without the welcome screen, extended:
        # writesettings = settings.Write('{"settings":{"zarafa":{"v1":{"main":{"language":"nl_NL.UTF-8","default_context":"mail","start_working_hour":540,"end_working_hour":1020,"week_start":1,"show_welcome":false},"contexts":{"mail":[],"calendar":{"default_zoom_level":30,"datepicker_show_busy":true}},"state":{"models":{"note":{"current_data_mode":0}},"contexts":{"mail":{"current_view":0,"current_view_mode":1}}}}}}}')

        writesettings = settings.Write(newSettings)
        if writesettings:
                print "Settings for user '%s' were applied." % sys.argv[1]
        else:
                print "Settings for user '%s' failed to be applied." % sys.argv[1]
        settings.Commit(0)

# Start program
if __name__ == "__main__":
        output = {}
        command_line_args()

        print args


#        orig_data = read_settings(username)
#        pprint.pprint(orig_data)
