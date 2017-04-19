#!/usr/bin/env python

from MAPI import *
from MAPI.Util import *
import sys, json, textwrap

def check_input():
        if len(sys.argv) < 2:
            sys.exit('Usage: %s username' % sys.argv[0])

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


# def check_input():
#         if len(sys.argv) < 2:
#             sys.exit('Usage: %s username < input_file' % sys.argv[0])

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

if __name__ == '__main__':
        output = {}
        print getTerminalSize()
        check_input()
        username = sys.argv[1]
        raw_data = read_settings(username)

        if raw_data:
            data = json.loads(str(raw_data)).get('settings',{}).get('zarafa',{}).get('v1',{}).get('contexts',{}).get('mail',{}).get('signatures',{})
            if 'all' in data:
                output[username] = data
            else:
                output[username] = { 'all':{}, 'new_message':None, 'replyforward_message':None }

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

            print "\n"
