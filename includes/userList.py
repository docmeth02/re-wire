import npyscreen
import curses
from includes import rewireFunctions


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
            for akey in range(0, self.maxheight-1):
                self.widgets[akey] = self.parent.add(userListText, name="%s-%s" % (self.parent.chat, akey),
                                                     relx=self.relx, rely=self.rely+akey,
                                                     value="", max_height=1, begin_entry_at=0,
                                                     max_width=self.width, width=self.width, editable=0)
                self.widgets[akey].hookparent(self)
                self.widgets[akey].add_handlers({curses.ascii.NL: self.widgets[akey].selected})
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
                self.users.append(UserListItem(self, int(auser.userid),
                                               decode(auser.nick), auser.status, int(auser.idle), acctype))
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
                self.users.append(UserListItem(self, int(auser.userid),
                                               decode(auser.nick), auser.status, int(auser.idle), acctype))
            self.updateList()
            return 1

    def refreshView(self):
        for awidget in self.widgets:
            if hasattr(awidget, 'display'):
                awidget.display()
        return

    def updateList(self):
        with self.parent.lock:
            colors = ['CURSOR', 'NO_EDIT', 'DANGER']
            i = 0
            for i in range(0, len(self.users)):
                if self.users[i].pos != i or self.users[i].isupdated:
                    name = decode(self.users[i].nick)
                    if self.users[i].isIdle:
                        name = "*%s" % name
                    self.widgets[i].value = name + " " * (self.width - len(name))
                    self.widgets[i].name = self.users[i].userid
                    self.widgets[i].editable = 1
                    self.widgets[i].color = colors[self.users[i].acctype]
                    self.parent.deferred_update(self.widgets[i], True)
                    self.users[i].pos = i
                    self.users[i].isupdated = 0
                i += 1
            if i != self.maxheight-1:
                for i in range(i, self.maxheight-1):
                    self.widgets[i].value = " " * self.width
                    self.widgets[i].name = 0
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
                        self.users[i].nick = decode(user.nick)
                        self.users[i].status = str(user.status)
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
                self.users.append(UserListItem(self, int(auser.userid),
                                               decode(auser.nick), auser.status, int(auser.idle), acctype))
                self.updateList()
                return 1
            return 0

    def itemSelected(self, userid):
        #npyscreen.notify_confirm(str(userid))
        user = self.parent.librewired.getUserByID(userid)
        options = ['Cancel', 'Start Private Chat', 'Send Message']
        if self.parent.librewired.privileges['getUserInfo']:
            options.append('Get User Info')
        if self.parent.librewired.privileges['kickUsers']:
            options.append('Kick')
        if self.parent.librewired.privileges['banUsers']:
            options.append('Ban')
        menu = npyscreen.Popup(name="User: %s" % decode(user.nick), framed=True, lines=len(options)+4, columns=25)
        menu.show_atx = self.parent.max_x-30
        menu.show_aty = 3
        selector = menu.add_widget(npyscreen.MultiLine, values=options, value=None, color="CURSOR",
                                   widgets_inherit_color=True,  slow_scroll=True, return_exit=True,
                                   select_exit=True, width=20)
        menu.display()
        selector.edit()
        if selector.value:
            value = options[selector.value]
            #npyscreen.notify_confirm(str(value))
            if 'Send Message' in value:
                message = rewireFunctions.composeMessage(userid)
                if message:
                    if not self.parent.sendPrivateMessage(int(userid), message):
                        return 0
                return 1
            if 'Start Private Chat' in value:
                if not self.parent.startPrivateChat(userid):
                    return 0
                return 1
            if 'Get User Info' in value:
                self.parent.openUserInfo(userid)
                return 1
            if "Kick" in value and self.parent.librewired.privileges['kickUsers']:
                kick = rewireFunctions.textDialog("Kick user %s" % decode(user.nick),
                                                  inputlabel="Enter message to show (optional):", oklabel="Kick")
                if kick:
                    if type(kick) is str:
                        msg = kick
                    else:
                        msg = ""
                    if not self.parent.kickUser(userid, msg):
                        return 0
            if "Ban" in value and self.parent.librewired.privileges['banUsers']:
                ban = rewireFunctions.textDialog("Ban user %s" % decode(user.nick),
                                                 inputlabel="Enter message to show (optional):", oklabel="Ban")
                if ban:
                    if type(ban) is str:
                        msg = ban
                    else:
                        msg = ""
                    if not self.parent.banUser(userid, msg):
                        return 0
                    return 1
        return

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
                    if decode(auser.nick) == decode(newnick):
                        return 0
                    return decode(auser.nick)
            return 0

    def yieldnicks(self):
        with self.parent.lock:
            nicks = []
            for auser in self.users:
                nicks.append(decode(auser.nick))
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


class userListText(npyscreen.FixedText):
    def hookparent(self, parent):
        self.userlist = parent

    def selected(self, *args, **kwargs):
        if self.name:
            self.userlist.itemSelected(self.name)
        return 1


def decode(s):
    try:
        s = unicode(s, errors='ignore')
    except:
        pass
    s = s.encode("UTF-8")
    return s
