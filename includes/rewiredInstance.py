import npyscreen
import curses
from librewired import rewiredclient
from includes import chatView, messageView
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

        self.msgview = 0
        self.msguserids = []
        self.msgnicks = {}
        self.msgs = {}

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
        self.librewired.appname = "re:wire"
        self.librewired.version = "WIP"
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
        self.librewired.notify("__ConnectionLost", self.connectionLost)
        self.librewired.notify("__Reconnected", self.reconnected)
        self.librewired.notify("__UserListDone", self.userListReady)
        self.librewired.notify("__PrivateMessage", self.gotPrivateMessage)

        formid = "%s-CHAT1" % (self.conID)
        self.chats[1] = chatView.chatview(self, formid, 1)  # init public chat

        if not self.librewired.connect(self.host, self.port):
            self.fail = 1
        if not self.fail:
            if not self.librewired.login(self.librewired.nick, self.login, self.pasword, True):
                self.fail = 2
        if self.fail:
            del self.chats[1]

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
            self.parent.setNextForm("MAIN")
        else:
            self.parent.setNextForm("%s-CHAT1" % (self.conID))
        self.parent.removeForm(formid)
        self.parent.switchFormNow()

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
        if "data:image" in chat[2]:
            if chat[2].count(chr(3)) == 2:
                chat[2] = chat[2][:chat[2].find(chr(3))]
            if chat[2].count(chr(128)):
                chat[2] = chat[2].replace(chr(128), '')
        if not len(chat[2]):
            return
        if int(chat[0]) in self.chats and nick:  # 2 = data
            self.chats[int(chat[0])].chatreceived(nick, chat[2], action)
        return

    def gotActionChat(self, chat):
        self.gotChat(chat, True)

    def sendChat(self, chatid, chat):
        try:
                chat = chat.encode("UTF-8")
        except:
                pass
        self.librewired.sendChat(int(chatid), chat)
        return

    def gotPrivateMessage(self, userid, message):
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
                curses.beep()
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
        self.parent.registerForm(form, self.parent.servers[self.conID].chats[chatid])
        self.parent.switchForm(form)
        self.chats[chatid].display()
        return

    def privateChatJoin(self, chatid):
        form = "%s-CHAT%s" % (self.conID, chatid)

        self.chats[chatid] = chatView.chatview(self, form, chatid)
        self.parent.servers[self.conID].forms.append(form)
        self.parent.registerForm(form, self.parent.servers[self.conID].chats[chatid])
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
            curses.beep()
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
        curses.beep()
        self.clientKicked(params, True)
