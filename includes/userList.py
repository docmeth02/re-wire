import npyscreen
import curses


class userlist():
    def __init__(self, parent, relx, rely, width, maxheight):
        self.parent = parent
        self.relx = relx
        self.rely = rely
        self.width = width
        self.maxheight = maxheight
        self.users = []
        self.widgets = {}

    def build(self, userlist, order):
        with self.parent.lock:
            if not self.parent.chat in order:
                npyscreen.notify_confirm("No such order: %s" % self.parent.chat)
                return 0
            for akey in range(0, self.maxheight):
                self.widgets[akey] = self.parent.add(npyscreen.FixedText, name="%s-%s" % (self.parent.chat, akey),
                                                     relx=self.relx, rely=self.rely+akey, value="", max_height=1,
                                                     max_width=self.width, width=self.width, editable=0)
                self.widgets[akey].add_handlers({curses.ascii.NL: self.itemSelected})
            for key in order[self.parent.chat]:
                auser = self.parent.librewired.getUserByID(key)
                if not auser:
                    continue
                acctype = 0
                if auser.login:
                    if auser.login.upper() != "GUEST":
                        acctype = 1
                if int(auser.admin):
                    acctype = 2
                self.users.append(UserListItem(self, int(auser.userid), auser.nick, auser.status, int(auser.idle), acctype))
            self.updateList()
            return 1

    def rebuildList(self, userlist, order):
        with self.parent.lock:
            self.users = []
            if not self.parent.chat in order:
                return 0
            for key in order[self.parent.chat]:
                auser = self.parent.librewired.getUserByID(key)
                if not auser:
                    continue
                acctype = 0
                if auser.login:
                    if auser.login.upper() != "GUEST":
                        acctype = 1
                if int(auser.admin):
                    acctype = 2
                self.users.append(UserListItem(self, int(auser.userid), auser.nick, auser.status, int(auser.idle), acctype))
            self.updateList()
            return 1

    def updateList(self):
        with self.parent.lock:
            colors = ['CURSOR', 'NO_EDIT', 'DANGER']
            i = 0
            for i in range(0, len(self.users)):
                if self.users[i].pos != i or self.users[i].isupdated:
                    name = self.users[i].nick
                    if self.users[i].isIdle:
                        name = "*%s" % name
                    self.widgets[i].value = name
                    self.widgets[i].editable = 1
                    self.widgets[i].color = colors[self.users[i].acctype]
                    self.parent.deferred_update(self.widgets[i], True)
                    self.users[i].pos = i
                    self.users[i].isupdated = 0
                i += 1
            if i != self.maxheight:
                for i in range(i, self.maxheight):
                    self.widgets[i].value = ""
                    self.widgets[i].color = ''
                    self.widgets[i].editable = 0
                    self.parent.deferred_update(self.widgets[i], True)
            return 1

    def removeUser(self, userid):
        with self.parent.lock:
            for i in range(len(self.users)):
                if self.users[i].userid == userid:
                    self.users.pop(i)
                    self.updateList()
                    return 1
            return 0

    def updateUser(self, userid):
        with self.parent.lock:
            i = 0
            for auser in self.users:
                if auser.userid == userid:
                    user = self.parent.librewired.getUserByID(userid)
                    if user:
                        acctype = 0
                        if user.login:
                            if user.login.upper() != "GUEST":
                                acctype = 1
                            if int(user.admin):
                                acctype = 2
                        self.users[i].nick = str(user.nick)
                        self.users[i].isIdle = int(user.idle)
                        self.users[i].acctype = acctype
                        self.users[i].isupdated = 1
                        self.updateList()
                        break
                i += 1

    def addUser(self, userid):
        with self.parent.lock:
            auser = self.parent.librewired.getUserByID(userid)
            if auser:
                acctype = 0
                if auser.login:
                    if auser.login.upper() != "GUEST":
                        acctype = 1
                if int(auser.admin):
                    acctype = 2
                self.users.append(UserListItem(self, int(auser.userid), auser.nick, auser.status, int(auser.idle), acctype))
                self.updateList()
                return 1
            return 0

    def itemSelected(self, *args):
        #npyscreen.notify_confirm(str(args))
        pass

    def checkStatusChanged(self, userid, newstatus):
        with self.parent.lock:
            for auser in self.users:
                if auser.userid == userid:
                    if auser.status == newstatus:
                        return 0
                    return 1
            return 1

    def checkNickChanged(self, userid, newnick):
        with self.parent.lock:
            for auser in self.users:
                if auser.userid == userid:
                    if auser.nick == newnick:
                        return 0
                    return auser.nick
            return 0

    def yieldnicks(self):
        with self.parent.lock:
            nicks = []
            for auser in self.users:
                nicks.append(auser.nick)
            return nicks


class UserListItem():
    def __init__(self, parent, userid, nick, status, isIdle=0, acctype=0):
        self.parent = parent
        self.userid = userid
        self.nick = nick
        self.status = status
        self.pos = -1
        self.isIdle = isIdle
        self.acctype = acctype  # guest / user / admin
        self.isupdated = 1
