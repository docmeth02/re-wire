import npyscreen
import curses
from includes import rewiredInstance


class NewConnection(npyscreen.FormBaseNew):
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.config = self.parent.config
        self.appliedBookmark = 'DEFAULT'
        self.formid = "MAIN"
        super(NewConnection, self).__init__(**kwargs)
        self.add_handlers({"^D": self.exit_application})
        self.add_handlers({"^Q": self.exit_application})
        self.add_handlers({"^T": self.parent.switchNextForm})
        self.add_handlers({curses.KEY_F1: self.parent.switchPrevForm})
        self.add_handlers({curses.KEY_F2: self.parent.switchNextForm})

    def create(self):
        start_x = int(round((self.max_x - 38) / 2))
        start_y = int(round((self.max_y - 5) / 2))
        self.name = "re:wire new connection"
        self.server = self.add(npyscreen.TitleText, relx=start_x, rely=start_y,
                               name="Server:      ", value="", field_width=20, begin_entry_at=16)
        self.user = self.add(npyscreen.TitleText, relx=start_x, rely=start_y+1,
                             name="Username:", value="", field_width=20, begin_entry_at=16)
        self.password = self.add(npyscreen.TitlePassword, relx=start_x, rely=start_y+2,
                                 name="Password: ", value="", field_width=20, begin_entry_at=16)
        self.reconnect = self.add(npyscreen.Checkbox, relx=start_x, rely=start_y+3,
                                  name="Reconnect automatically")
        self.connect = self.add(npyscreen.ButtonPress, relx=start_x+6, rely=start_y+4,
                                name="Connect")
        self.quit = self.add(npyscreen.ButtonPress, relx=start_x+16, rely=start_y+4, name="Quit")
        self.quit.handle_mouse_event = self.handle_mouse_event
        self.quit.whenPressed = self.exit_application
        self.connect.whenPressed = self.doConnect
        self.chooseBookmark = self.add(npyscreen.ButtonPress, relx=start_x+8, rely=start_y+6, name="Open Bookmark")
        self.chooseBookmark.whenPressed = self.openBookmarks

        self.editw = 4  # focus connect button
        self.applyBookmark('DEFAULT')  # make sure we display something even when the config file is messed up
        if self.config.has_section('defaults'):
            self.applyBookmark('defaults')
            self.appliedBookmark = 'defaults'

    def exit_application(self, *args):
        self.parent.shutdown()
        curses.beep()
        self.parentApp.setNextForm(None)
        self.editing = False
        raise SystemExit

    def handle_mouse_event(self, mouse_event):
        mouse_id, rel_x, rel_y, z, bstate = self.quit.interpret_mouse_event(mouse_event)
        npyscreen.notify_confirm(str(self.quit.interpret_mouse_event(mouse_event)))

    def backspace(self, *args):
        curses.beep()

    def openBookmarks(self, *args, **kwargs):
        servers = []
        for aserver in self.config.sections():
            if aserver != "defaults" and aserver != "settings":
                servers.append(aserver)
        self.bookmarkview = bookmarkPopUp(self, servers)
        self.parent.registerForm("BOOKMARKSELECT", self.bookmarkview.build())
        self.parent.switchForm("BOOKMARKSELECT")

    def closeBookmarks(self):
        self.parent.switchForm("MAIN")
        self.parent.removeForm("BOOKMARKSELECT")
        del(self.bookmarkview)

    def applyBookmark(self, bookmarkname):
        if not self.config.has_section(bookmarkname):
            if bookmarkname != "DEFAULT":
                curses.beep()
                return 0
        self.server.value = self.config.get(bookmarkname, 'server')
        if int(self.config.get(bookmarkname, 'port')) != 2000:
            self.server.value += ":" + str(self.config.get(bookmarkname, 'port'))
        self.user.value = self.config.get(bookmarkname, 'user')
        self.password.value = self.config.get(bookmarkname, 'password')
        self.reconnect.value = int(self.config.get(bookmarkname, 'autoreconnect'))
        self.appliedBookmark = bookmarkname
        self.editw = 4
        return 1

    def doConnect(self, *args):
        if not self.server.value:
            self.server.edit()
            return 0
        server = self.server.value
        port = 2000
        if ':' in server:
            server, port = server.split(':', 1)
            try:
                port = int(port)
            except:
                self.server.edit()
                return 0
        if not self.user.value:
            self.user.edit()
            return 0
        user = self.user.value
        password = self.password.value
        autoreconnect = int(self.reconnect.value)
        conID = self.parent.conID
        self.parent.conID += 1
        self.parent.servers[conID] = rewiredInstance.rewiredInstance(self.parent,
                                                                     conID, server, port, user, password, autoreconnect,
                                                                     self.appliedBookmark)
        if self.parent.servers[conID].fail:
            if self.parent.servers[conID].fail == 1:
                npyscreen.notify_confirm("Failed to connect to %s" % server, "Failed to connect")
            if self.parent.servers[conID].fail == 2:
                npyscreen.notify_confirm("Login Failed", "Login Failed")
            self.parent.servers[conID].librewired.keepalive = 0
            del(self.parent.servers[conID])
            return 0
        form = "%s-CHAT1" % (conID)
        self.parent.servers[conID].forms.append(form)
        self.parent.registerForm(form, self.parent.servers[conID].chats[1])
        self.applyBookmark('DEFAULT')
        self.appliedBookmark = 'DEFAULT'
        if self.config.has_section('defaults'):
            self.applyBookmark('defaults')
            self.appliedBookmark = 'defaults'
        self.parent.switchForm(form)

    def runAutoconnect(self):
        for aserver in self.config.sections():
            if aserver != "defaults":
                if int(self.config.get(aserver, 'connectonstart')):
                    self.autoconnect(aserver)

    def autoconnect(self, bookmarkname, switchTo=False):
        if not self.config.has_section(bookmarkname):
            return 0

        server = self.config.get(bookmarkname, 'server')
        port = self.config.get(bookmarkname, 'port')
        user = self.config.get(bookmarkname, 'user')
        password = self.config.get(bookmarkname, 'password')
        autoreconnect = int(self.config.get(bookmarkname, 'autoreconnect'))

        conID = self.parent.conID
        self.parent.conID += 1
        self.parent.servers[conID] = rewiredInstance.rewiredInstance(self.parent,
                                                                     conID, server, port, user, password, autoreconnect,
                                                                     bookmarkname)
        if self.parent.servers[conID].fail:
            if self.parent.servers[conID].fail == 1:
                npyscreen.notify_confirm("Failed to connect to %s" % server, "Failed to connect")
            if self.parent.servers[conID].fail == 2:
                npyscreen.notify_confirm("Login Failed", "Login Failed")
            self.parent.servers[conID].librewired.keepalive = 0
            del(self.parent.servers[conID])
            return 0
        form = "%s-CHAT1" % (conID)
        self.parent.servers[conID].forms.append(form)
        self.parent.registerForm(form, self.parent.servers[conID].chats[1])
        if switchTo:
            self.parent.switchForm(form)


class bookmarkPopUp():
    def __init__(self, parent, servers):
        self.parent = parent
        self.servers = servers
        self.value = False

    def build(self):
        self.popup = npyscreen.FormBaseNew(name="Select a Bookmark", framed=True, relx=5, rely=5, lines=12, columns=60)
        self.popup.show_atx = 10
        self.popup.show_aty = 2

        self.select = self.popup.add_widget(npyscreen.MultiLineAction, name="Select Bookmark", max_height=7, height=7,
                                            values=self.servers,  value=self.value, return_exit=True, select_exit=True)
        self.select.actionSelected = self.actionSelected
        self.select.actionHighlighted = self.actionHighlighted
        self.cancel = self.popup.add(npyscreen.ButtonPress, relx=45, rely=9, name="Cancel")
        self.cancel.whenPressed = self.close
        return self.popup

    def actionSelected(self, act_on_these, keypress):
        self.actionHighlighted(act_on_these, keypress)

    def actionHighlighted(self, selection, key_press):
        if self.parent.applyBookmark(selection):
            self.close()

    def close(self, *args, **kwargs):
        self.parent.closeBookmarks()
