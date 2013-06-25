import npyscreen
import curses
from includes import commandHandler, userList, autoCompleter
from textwrap import wrap
from threading import RLock
from time import strftime


class chatview(npyscreen.FormMutt):
    def __init__(self, parent, formid, chatid, **kwargs):
        self.chat = chatid
        self.parent = parent
        self.formid = formid
        self.lock = RLock()
        self.chattopic = 0
        self.notification = 0
        self.userlist = 0
        self.librewired = self.parent.librewired
        self.defaultHandlers = {curses.KEY_F1: self.parent.prevForm,
                                curses.KEY_F2: self.parent.nextForm,
                                curses.KEY_F3: self.parent.openMessageView,
                                curses.KEY_F4: self.parent.openNewsView}
        self.validCommands = ['/nick', '/status', '/ping', '/icon', '/topic', '/me', '/clear', '/clear-all',
                              '/afk', '/away', '/back', '/afk-all', '/away-all', '/back-all']
        self.commandHandler = commandHandler.commandhandler(self, self.librewired)
        super(chatview, self).__init__(**kwargs)
        self.add_handlers({"^D": self.closeForm})
        self.add_handlers({"^T": self.parent.nextForm})
        self.add_handlers(self.defaultHandlers)

    def beforeEditing(self):
        if self.userlist:  # redraw userlist on chatview activation
            self.userlist.refreshView()

    def create(self):
        chat = "Public Chat"
        if self.chat != 1:
            chat = "Private Chat %s" % self.chat
        self.name = "re:wire @%s: %s " % (self.parent.host, chat)
        self.title = self.add(npyscreen.FixedText, name="title", editable=0, rely=0, value=self.name)
        self.box = self.add(npyscreen.Pager, rely=2, relx=0, width=self.max_x - 18, height=self.max_y - 4,
                            max_width=self.max_x - 17, max_height=self.max_y - 2, editable=1, color="CURSOR",
                            widgets_inherit_color=True)
        self.userlist = userList.userlist(self, self.max_x - 17, 1, 16, self.max_y - 3)

        self.topic = self.add(npyscreen.TitleText, name="Topic:", value="", begin_entry_at=9, hidden=1,
                              relx=0, rely=1, editable=False, max_width=self.max_x - 20, color="NO_EDIT")
        self.topic.label_widget.hidden = 1

        self.chatlabel = self.add(npyscreen.TitleText, name="Chat: ", relx=0, rely=self.max_y - 1, editable=False)
        self.chatinput = self.add(autoCompleter.autocompleter, relx=6, rely=self.max_y - 1,
                                  begin_entry_at=1, max_width=self.max_x - 17, name="%s-%s" % (self.formid, self.chat))

        self.chatinput.hookParent(self)
        self.chatinput.add_handlers({curses.ascii.NL: self.chatentered})
        self.chatinput.add_handlers({curses.KEY_ENTER: self.chatinputenter})
        self.chatinput.add_handlers({curses.KEY_BACKSPACE: self.chatinput.backspace})
        self.chatinput.add_handlers({'^A': self.chatinput.cursorLeft})
        self.chatinput.add_handlers({'^E': self.chatinput.cursorRight})
        self.chatinput.add_handlers(self.defaultHandlers)
        self.editw = 4

    def deferred_update(self, instance, forced):
        if self.parent.getActiveForm() == self.formid:  # we're active right now
            if forced:
                instance.display()
            else:
                instance.update()
            return 1
        # since we are not the active form, there is no need to update the screen
        return 0

    def chatentered(self, *args, **kwargs):
        action = 0
        if 'action' in kwargs:
            action = int(kwargs['action'])
        self.chatinput.lastcomplete = 0
        self.chatinput.laststr = 0
        chat = self.chatinput.value
        if chat:
            if not self.commandHandler.checkCommand(chat):
                self.parent.sendChat(self.chat, chat, action)
        self.chatinput.value = ""

    def chatinputenter(self, *args):
        self.chatentered(self, action=True)

    def focusInput(self, *args):
        self.chatinput.edit()

    def chatreceived(self, nick, chat, action):
        if action:
            self.appendChat("*** %s %s" % (str(nick), str(chat)))
        else:
            self.appendChat(str(chat), str(nick))

    def appendChat(self, chat, nick=False):
        curtime = ""
        if int(self.parent.config.get('settings', 'timestampchat')):
            try:
                curtime = strftime(self.parent.config.get('settings', 'timeformat'))
            except Exception:  # save default
                curtime = strftime('[%H:%M]')
        nicktext = ""
        if nick:
            nicktext = " %s" % nick
        header = "%s%s" % (curtime, nicktext)
        if len(header):
            header += ": "
        lines = [chat]
        if (len(header) + len(chat)) >= (self.box.width - 1):
            lines = wrap(chat, (self.box.width - 1) - len(header))
        for i in range(0, len(lines)):
            if not i:
                self.box.values.append(header + lines[i])
                continue
            self.box.values.append((" " * len(header)) + lines[i])
        self.box.h_show_end("")
        self.deferred_update(self.box, True)

    def updateTopic(self, topic):
        self.topic.value = topic
        self.chattopic = topic
        if not self.topic.value:
            self.topic.hidden = 1
            self.topic.label_widget.hidden = 1
        elif self.topic.hidden or self.topic.label_widget.hidden:
            self.topic.entry_widget.color = 'DEFAULT'
            self.topic.hidden = 0
            self.topic.label_widget.hidden = 0
        self.deferred_update(self.topic, True)
        self.deferred_update(self.topic.label_widget, True)
        return

    def closeForm(self, *args):
        self.librewired.leaveChat(self.chat)
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)

    def onTimer(self):
        if len(self.parent.notifications):
            if self.notification > len(self.parent.notifications) - 1:
                self.notification = -1

            if not self.chattopic and self.notification < 0:
                self.notification = 0

            if self.notification == -1:
                self.updateTopic(self.chattopic)
                self.notification = 0
                return

            notification = self.parent.notifications[self.notification]
            label = notification.label
            if notification.count and "%s" in notification.label:
                label = notification.label % notification.count
            self.topic.value = label
            self.topic.hidden = 0
            self.topic.entry_widget.color = notification.color
            self.deferred_update(self.topic, True)
            self.topic.label_widget.hidden = 1
            self.deferred_update(self.topic.label_widget, True)
            self.notification += 1
            return

        else:
            if self.chattopic and self.notification != -1:
                self.updateTopic(self.chattopic)
                self.notification = -1
                return
            elif not self.chattopic:
                if not self.topic.hidden or not self.topic.label_widget.hidden:
                    self.topic.hidden = 1
                    self.topic.label_widget.hidden = 1
                    self.deferred_update(self.topic)
                    self.deferred_update(self, topic.label_widget)
        return

    def sendPrivateMessage(self, userid, message):
        return self.parent.sendPrivateMessage(userid, message)

    def startPrivateChat(self, userid):
        return self.parent.startPrivateChat(userid)

    def kickUser(self, id, msg=""):
        return self.parent.kickUser(id, msg)

    def banUser(self, id, msg=""):
        return self.parent.banUser(id, msg)

    def openUserInfo(self, userid):
        return self.parent.openUserInfo(userid)

    def applyCommandToAll(self, command):
        return self.parent.applyCommandToAll(command)


class chatInvite(npyscreen.FormBaseNew):
    def __init__(self, parent, formid, chatid, user, **kwargs):
        self.chat = chatid
        self.chatparent = parent
        self.formid = formid
        self.user = user
        super(chatInvite, self).__init__(relx=5, rely=5, lines=12, columns=60, **kwargs)
        self.show_atx = 10
        self.show_aty = 2

    def create(self):
        self.name = "re:wire @%s" % (self.chatparent.host)
        self.add_handlers({curses.KEY_F3: self.closeForm})
        self.add_handlers({curses.KEY_F1: self.chatparent.prevForm})
        self.add_handlers({curses.KEY_F2: self.chatparent.nextForm})
        self.label = self.add_widget(npyscreen.FixedText, name="label", editable=0,
                                     value="User %s has invited you to a private chat" % self.user.nick)
        self.join = self.add_widget(npyscreen.ButtonPress, name="Join", relx=12, rely=5)
        self.join.whenPressed = self.doJoin
        self.ignore = self.add_widget(npyscreen.ButtonPress, name="Ignore", relx=21, rely=5)
        self.ignore.whenPressed = self.doIgnore
        self.decline = self.add_widget(npyscreen.ButtonPress, name="Decline", relx=32, rely=5)
        self.decline.whenPressed = self.doDecline
        self.editw = 1

    def closeForm(self, *args, **kwargs):
        self.editable = False
        self.editing = False
        self.chatparent.closeForm(self.formid)

    def doJoin(self, *args, **kwargs):
        if not self.chatparent.librewired.joinPrivateChat(self.chat):
            return 0
        self.chatparent.closeForm(self.formid)
        self.chatparent.privateChatJoin(self.chat)

    def doIgnore(self, *args, **kwargs):
        self.closeForm()

    def doDecline(self, *args, **kwargs):
        self.chatparent.librewired.declinePrivateChat(self.chat)
        self.closeForm()
