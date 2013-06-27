import npyscreen
import curses
from librewired import rewiredclient
from includes import chatView, messageView, userinfoView, newsView, rewireFunctions
rewireMsg = messageView.rewireMsg
from sys import argv
from os import path
from time import sleep, time


class rewiredInstance():
    def __init__(self, parent, conID, host, port, login, password, autoreconnect, profile):
        self.parent = parent
        self.config = parent.config
        self.conID = conID
        self.host = host
        self.port = port
        self.login = login
        self.forms = []
        self.pasword = password
        if not password:
            self.password = ""
        self.autoreconnect = autoreconnect
        self.shutdown = 0
        self.librewired = rewiredclient.client(self)
        self.homepath = path.dirname(argv[0])

        self.newsview = 0

        self.msgview = 0
        self.msguserids = []
        self.msgnicks = {}
        self.msgs = {}

        self.notifications = []

        icon = self.config.get(profile, 'icon')
        if not icon:
            if path.exists(path.join(self.homepath, "data/default.png")):
                self.librewired.loadIcon(path.join(self.homepath, "data/default.png"))
        else:
            if not path.exists(icon):
                icon = path.join(self.homepath, icon)
            if path.exists(icon):
                self.librewired.loadIcon(icon)
        self.librewired.nick = self.config.get(profile, 'nick')
        self.librewired.appname = self.parent.appname
        self.librewired.version = self.parent.version
        self.librewired.status = self.config.get(profile, 'status')
        self.librewired.autoreconnect = self.autoreconnect
        self.librewired.start()
        self.chats = {}
        self.fail = 0

        # setup lib:rewired handlers
        self.librewired.notify("__ClientLeave", self.clientLeft)
        self.librewired.notify("__ClientKicked", self.clientKicked)
        self.librewired.notify("__ClientBanned", self.clientBanned)
        self.librewired.notify("__ClientJoin", self.updateUserList)
        self.librewired.subscribe(300, self.gotChat)
        self.librewired.subscribe(301, self.gotActionChat)
        self.librewired.notify("__ClientStatusChange", self.statusChange)
        self.librewired.notify("__ChatTopic", self.gotChatTopic)
        self.librewired.notify("__PrivateChatInvite", self.privateChatInvite)
        self.librewired.notify("__PrivateChatDecline", self.privateChatDecline)
        self.librewired.notify("__ConnectionLost", self.connectionLost)
        self.librewired.notify("__Reconnected", self.reconnected)
        self.librewired.notify("__UserListDone", self.userListReady)
        self.librewired.notify("__PrivateMessage", self.gotPrivateMessage)
        self.librewired.notify("__NewsPosted", self.gotNewsPosted)

        formid = "%s-CHAT1" % (self.conID)
        self.chats[1] = chatView.chatview(self, formid, 1)  # init public chat

        self.max_x = self.chats[1].max_x
        self.max_y = self.chats[1].max_y

        if not self.librewired.connect(self.host, self.port):
            self.fail = 1
        if not self.fail:
            if not self.librewired.login(self.librewired.nick, self.login, self.pasword, True):
                self.fail = 2
        if self.fail:
            del self.chats[1]
        self.librewired.getNews()

    def userListReady(self, msg):
        chatid = msg[0]
        if int(chatid) in self.chats:
            self.chats[chatid].userlist.build(self.librewired.userlist, self.librewired.userorder)

    def closeForm(self, formid):
        for i in range(0, len(self.forms)):
            if self.forms[i] == formid:
                self.forms.pop(i)
                break
        if formid == "%s-CHAT1" % (self.conID):
            # public chat close means disconnect and shutdown this connection
            self.librewired.disconnect()
            self.librewired.keepalive = 0
            if not self.librewired.join(5):
                pass  # error?
            for aform in self.forms:
                if type(aform) is not str:
                    self.parent.removeForm(aform.formid)
            self.parent.removeConnection(self.conID)
            self.parent.switchNextForm()
            return 1
        self.parent.removeForm(formid)
        self.parent.switchForm("%s-CHAT1" % self.conID)  # back to public chat

    def nextForm(self, *args):
        self.parent.switchNextForm()
        return 1

    def prevForm(self, *args):
        self.parent.switchPrevForm()
        return 1

    def switchForm(self, formid):
        self.parent.switchForm(formid)

    def gotChat(self, chat, action=False):
        chat = chat.msg
        nick = self.librewired.getNickByID(int(chat[1]))
        text = rewireFunctions.checkssWiredImage(chat[2])
        if not len(text):
            return
        if int(chat[0]) in self.chats and nick:  # 2 = data
            self.chats[int(chat[0])].chatreceived(nick, text, action)
        return

    def gotActionChat(self, chat):
        self.gotChat(chat, True)

    def sendChat(self, chatid, chat, action=False):
        try:
                chat = chat.encode("UTF-8")
        except:
                pass
        self.librewired.sendChat(int(chatid), chat, action)
        return

    def gotPrivateMessage(self, userid, message):
        message = rewireFunctions.checkssWiredImage(message)
        if not message:
            return 0
        userid = int(userid)
        user = self.librewired.getUserByID(userid)
        if not user:
            return 0
        if not userid in self.msguserids:
            self.msguserids.append(userid)
            self.msgnicks[userid] = user.nick
        if not userid in self.msgs:
            self.msgs[userid] = []
        try:
            msg = rewireMsg(userid, user.nick, time(), message)
            self.msgs[userid].append(msg)
        except:
            return 0
        if self.msgview:
            self.msgview.updateSidebar()
        curses.beep()
        self.addNotification('MSG', '%s unread messages from '
                             + str(user.nick), 1, userid, color='NO_EDIT')
        return 1

    def sendPrivateMessage(self, userid, message):
        userid = int(userid)
        if not self.librewired.sendPrivateMsg(userid, message):
            return 0
        return 1

    def statusChange(self, msg):
        userid = int(msg)
        user = self.librewired.getUserByID(userid)
        for akey, achat in self.chats.items():
            for auser in achat.userlist.users:
                if int(auser.userid) == int(userid):
                    oldnick = achat.userlist.checkNickChanged(userid, user.nick)
                    if oldnick:
                            achat.appendChat(">>> %s changed name to %s <<<" % (oldnick, user.nick))
                            achat.userlist.updateUser(userid)
                    elif achat.userlist.checkStatusChanged(userid, user.status):
                        achat.appendChat(">>> %s changed status to %s <<<" % (user.nick, user.status))
                        achat.userlist.updateUser(userid)
                    else:
                        achat.userlist.updateUser(userid)

    def updateUserList(self, msg, leave=False, client=False):
        try:
            userid = int(msg[0])
            chatid = int(msg[1])
        except:
            npyscreen.notify_confirm("Error in updateUserList: " + str(msg), title="updateUserList")
            return 0
        if chatid in self.chats:
            if leave:
                self.chats[chatid].userlist.removeUser(userid)
                self.chats[chatid].appendChat(">>> %s left <<<" % client['nick'])
            else:
                self.chats[chatid].userlist.addUser(userid)
                nick = self.librewired.getNickByID(userid)
                self.chats[chatid].appendChat(">>> %s joined <<<" % nick)
        return 1

    def privateChatInvite(self, chatid, userid):
        chatid = int(chatid)
        userid = int(userid)
        user = self.librewired.getUserByID(userid)
        form = "%s-CHAT%s" % (self.conID, chatid)

        self.chats[chatid] = chatView.chatInvite(self, form, chatid, user)
        self.parent.servers[self.conID].forms.append(form)
        self.parent.registerForm(form, self.chats[chatid])
        self.parent.switchForm(form)
        self.chats[chatid].display()
        return

    def privateChatDecline(self, chatid, userid):
        user = self.librewired.getUserByID(int(userid))
        if not user:
            return 0
        if int(chatid) in self.chats:
            self.chats[int(chatid)].appendChat(">>> %s has declined invitation <<<" % user.nick)
        return

    def startPrivateChat(self, userid):
        privatechatid = self.librewired.startPrivateChat()
        if not privatechatid:
            return 0
        if not self.librewired.invitePrivateChat(privatechatid, userid):
            return 0
        self.privateChatJoin(privatechatid)
        return 1

    def privateChatJoin(self, chatid):
        form = "%s-CHAT%s" % (self.conID, chatid)

        self.chats[chatid] = chatView.chatview(self, form, chatid)
        self.parent.servers[self.conID].forms.append(form)
        self.parent.registerForm(form, self.chats[chatid])
        self.chats[chatid].userlist.build(self.librewired.userlist, self.librewired.userorder)
        self.parent.switchForm(form)
        self.chats[chatid].display()
        return

    def openMessageView(self, *args, **kwargs):
        formid = "MESSAGES-%s" % self.conID
        if self.msgview:
            self.switchForm(formid)
            return
        self.msgview = messageView.messageview(self, formid)
        self.parent.registerForm(formid, self.msgview.build())
        self.parent.switchForm(formid)
        return

    def openNewsView(self, *args, **kwargs):
        formid = "NEWS-%s" % self.conID
        if self.newsview:
            self.switchForm(formid)
            return
        self.newsview = newsView.newsview(self, formid)
        self.parent.registerForm(formid, self.newsview.build())
        self.parent.switchForm(formid)
        return

    def gotNewsPosted(self, newsobj):
        if self.newsview:
            self.newsview.populate()
            return 1
        self.addNotification('NEWS', 'New News got posted', 0, -1, color='NO_EDIT')
        pass

    def clientLeft(self, msg, client):
        self.updateUserList(msg, True, client)
        return

    def gotChatTopic(self, msg):
        if msg[0] in self.chats:
            self.chats[msg[0]].updateTopic(msg[1]['text'])
        return

    def getActiveForm(self):
        try:
            form = self.parent.returnActiveForm()
        except AttributeError:
            curses.beep()
            return 0
        return form

    def connectionLost(self):
        for akey, achat in self.chats.items():
            achat.userlist.users = []
            achat.appendChat(">>> lost connection to %s <<<" % self.host)
        return

    def reconnected(self):
        for akey, achat in self.chats.items():
            achat.userlist.rebuildList(self.librewired.userlist, self.librewired.userorder)
            achat.appendChat(">>> reconnected to %s successfully <<<" % self.host)
        return

    def clientKicked(self, params, ban=False):
        killerid, victimid, text = params
        victim = self.librewired.getUserByID(int(victimid))
        if int(victimid) == int(self.librewired.id):
            with self.librewired.lock:
                self.librewired.autoreconnect = 0
        killer = self.librewired.getUserByID(int(killerid))
        if text:
            text = ": %s" % text
        msg = ">>> %s was kicked by %s%s <<<"
        if ban:
            msg = ">>> %s was banned by %s%s <<<"
        for akey, achat in self.chats.items():
            achat.appendChat(msg % (victim.nick, killer.nick, text))
        return

    def clientBanned(self, params):
        self.clientKicked(params, True)

    def addNotification(self, nftype, label, count, ident, color='DEFAULT'):
        for i in range(len(self.notifications)):
            if self.notifications[i].nftype == nftype and self.notifications[i].ident == ident:
                    self.notifications[i].label = label
                    self.notifications[i].count = self.notifications[i].count + count
                    return 1
        self.notifications.append(rewireNotification(nftype, label, count, ident, color))
        return 1

    def removeNotification(self, nftype, removecount, ident):
        for i in range(0, len(self.notifications)):
            if self.notifications[i].nftype == nftype and self.notifications[i].ident == ident:
                if removecount == -1:
                    self.notifications.pop(i)
                    break
                self.notifications[i].count = self.notifications[i].count - removecount
                if not self.notifications[i].count:
                    self.notifications.pop(i)
                return 1
        return 0

    def kickUser(self, id, msg=""):
        return self.librewired.kickUser(id, msg)

    def banUser(self, id, msg=""):
        return self.librewired.banUser(id, msg)

    def openUserInfo(self, userid):
        formid = "INFO-%s-%s" % (self.conID, userid)
        if formid in self.forms:
            self.parent.switchForm(formid)
            return
        view = userinfoView.userinfoview(self, userid, formid)
        self.parent.registerForm(formid, view.build())
        self.parent.switchForm(formid)
        view.populate()
        return

    def applyCommandToAll(self, command):
        return self.parent.applyCommandToAll(command)

    def checkCommand(self, command):
        for aform in self.forms:
            if type(self.parent._Forms[aform]) is chatView.chatview:
                if hasattr(self.parent._Forms[aform], 'commandHandler'):
                    self.parent._Forms[aform].commandHandler.checkCommand(command)


class rewireNotification():
    def __init__(self, nftype, label, count, ident, color='DEFAULT'):
        self.nftype = nftype
        self.label = label
        self.count = count
        self.ident = ident
        self.date = time()
        self.color = color
