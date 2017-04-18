#!/usr/bin/env python

from MAPI.Util import *

session = OpenECSession('SYSTEM','', os.getenv('ZARAFA_SOCKET', 'file:///var/run/zarafa'), flags=0)

def GetGuids(session, users = None, flags = 0):
    """<session> [<users>] [<flags>]

    Returns the store guid for given user(s) within the current <session>.
    """
    ems = GetDefaultStore(session).QueryInterface(IID_IExchangeManageStore)
    if users is None:
        users = GetUserList(session)
    elif isinstance(users, basestring):
        users = [users]

    for user in users:
        try:
            storeid = ems.CreateStoreEntryID(None, user, 0)
            store = session.OpenMsgStore(0, storeid, IID_IMsgStore, flags)
            storeguid = HrGetOneProp(store, PR_STORE_RECORD_KEY).Value.encode('hex').upper()

        # The following excepts are mainly to prevent errors in multi-server setups.
        # This script will be made SSL capable in the future.
        except MAPIErrorNotFound:
            continue
        except MAPIErrorLogonFailed:
            continue
        except MAPIErrorNetworkError:
            continue
        yield storeguid

users = []
guids = []

[users.append(row) for row in GetUserList(session) if row not in ["SYSTEM", "Everyone"]]
[guids.append(row) for row in GetGuids(session, users)]

for user,guid in zip(users,guids):
    print "%s %s" % (guid,user)
