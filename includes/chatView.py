import npyscreen
import curses
from includes import commandHandler, userList, autoCompleter
from textwrap import wrap
from threading import RLock


class chatview(npyscreen.FormMutt):
    def __init__(self, parent, formid, chatid, **kwargs):
        self.chat = chatid
        self.parent = parent
        self.formid = formid
        self.lock = RLock()
        self.chattopic = 0
        self.librewired = self.parent.librewired
        self.defaultHandlers = {curses.KEY_F1: self.parent.prevForm,
                                curses.KEY_F2: self.parent.nextForm,
                                curses.KEY_F3: self.parent.openMessageView}
        self.validCommands = ['/nick', '/status', '/ping', '/icon', '/topic', '/me', '/clear']
        self.commandHandler = commandHandler.commandhandler(self, self.librewired)
        super(chatview, self).__init__(**kwargs)
        self.add_handlers({"^D": self.closeForm})
        self.add_handlers({"^T": self.parent.nextForm})
        self.add_handlers(self.defaultHandlers)

    def create(self):
        chat = "Public Chat"
        if self.chat != 1:
            chat = "Private Chat %s" % self.chat
        self.name = "re:wire @%s: %s " % (self.parent.host, chat)
        self.title = self.add(npyscreen.FixedText, name="title", editable=0, rely=0, value=self.name)
        self.box = self.add(npyscreen.Pager, rely=1, relx=0, width=self.max_x - 18, height=self.max_y - 4,
                            max_width=self.max_x - 17, max_height=self.max_y - 3, editable=1, color="CURSOR",
                            widgets_inherit_color=True)
        self.userlist = userList.userlist(self, self.max_x - 17, 1, 16, self.max_y - 3)

        self.topic = self.add(npyscreen.TitleText, name="Topic:", value="", begin_entry_at=9, hidden=1,
                              relx=0, rely=self.max_y - 3, editable=False, max_width=self.max_x - 20)
        self.topic.label_widget.hidden = 1

        self.chatlabel = self.add(npyscreen.TitleText, name="Chat: ", relx=0, rely=self.max_y - 1, editable=False)
        self.chatinput = self.add(autoCompleter.autocompleter, relx=6, rely=self.max_y - 1,
                                  begin_entry_at=1, max_width=self.max_x - 17, name="%s-%s" % (self.formid, self.chat))

        self.chatinput.hookParent(self)
        self.chatinput.add_handlers({curses.ascii.NL: self.chatinputenter})
        self.chatinput.add_handlers({curses.KEY_BACKSPACE: self.chatinput.backspace})
        self.chatinput.add_handlers({curses.KEY_F3: self.parent.openMessageView})
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

    def chatinputenter(self, *args):
        self.chatinput.lastcomplete = 0
        self.chatinput.laststr = 0
        chat = self.chatinput.value
        if chat:
            if not self.commandHandler.checkCommand(chat):
                self.parent.sendChat(self.chat, chat)
        self.chatinput.value = ""

    def focusInput(self, *args):
        self.chatinput.edit()

    def chatreceived(self, nick, chat, action):
        if action:
            self.appendChat("*** %s %s" % (str(nick), str(chat)))
        else:
            self.appendChat(str(chat), str(nick))

    def appendChat(self, chat, nick=False):
        length = len(chat)
        width = self.box.width
        if nick:
            length += len(nick)+2
        if length > width:
            if nick:
                lines = wrap(chat, width - (len(nick) + 2))
                for i in range(0, len(lines)):
                    if not i:
                        lines[i] = "%s: %s" % (nick, lines[i])
                    else:
                        spacing = " " * (len(nick) + 2)
                        lines[i] = spacing + lines[i]
            else:
                lines = wrap(chat, width)
        else:
            if nick:
                chat = "%s: %s" % (nick, chat)
            lines = [chat]
        for achat in lines:
            self.box.values += [achat]
        self.box.h_show_end("")
        self.deferred_update(self.box, True)

    def updateTopic(self, topic):
        self.topic.value = topic
        if not self.topic.value:
            self.topic.hidden = 1
            self.topic.label_widget.hidden = 1
        elif self.topic.hidden or self.topic.label_widget.hidden:
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


class chatInvite(npyscreen.FormBaseNew):
    def __init__(self, parent, formid, chatid, user, **kwargs):
        self.chat = chatid
        self.parent = parent
        self.formid = formid
        self.user = user
        super(chatInvite, self).__init__(relx=5, rely=5, lines=12, columns=60, **kwargs)
        self.show_atx = 10
        self.show_aty = 2

    def create(self):
        self.name = "re:wire @%s" % (self.parent.host)
        self.add_handlers({"^T": self.parent.nextForm})
        self.add_handlers({"^D": self.closeForm})
        self.label = self.add(npyscreen.FixedText, name="label", editable=0,
                              value="User %s has invited you to a private chat" % self.user.nick)
        self.join = self.add(npyscreen.ButtonPress, name="Join", relx=12, rely=5)
        self.join.whenPressed = self.doJoin
        self.ignore = self.add(npyscreen.ButtonPress, name="Ignore", relx=21, rely=5)
        self.ignore.whenPressed = self.doIgnore
        self.decline = self.add(npyscreen.ButtonPress, name="Decline", relx=32, rely=5)
        self.decline.whenPressed = self.doDecline

    def closeForm(self, *args):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)

    def doJoin(self, *args, **kwargs):
        if not self.parent.librewired.joinPrivateChat(self.chat):
            curses.beep()
            return 0
        self.parent.closeForm(self.formid)
        self.parent.privateChatJoin(self.chat)

    def doIgnore(self, *args, **kwargs):
        self.closeForm()

    def doDecline(self, *args, **kwargs):
        self.parent.librewired.declinePrivateChat(self.chat)
        self.closeForm()
