from includes import rewireFunctions
from os.path import basename
from threading import Timer
from time import time
import npyscreen
import curses


class userinfoview():
    def __init__(self, parent, userid, formid):
        self.parent = parent
        self.formid = formid
        self.userid = int(userid)
        self.max_x = self.parent.max_x
        self.max_y = self.parent.max_y
        self.width = 45  # int(self.max_x/1.5)
        self.height = self.max_y - 3
        self.refreshtimer = 0

    def build(self):
        user = self.parent.librewired.getUserByID(self.userid)
        self.popup = npyscreen.FormBaseNew(name="%s Info" % user.nick,
                                           framed=True, lines=self.height, columns=self.width)
        self.popup.formid = self.formid
        self.popup.show_atx = int((self.max_x - self.width) / 2)
        self.popup.show_aty = 1
        self.popup.add_handlers({curses.KEY_F1: self.parent.prevForm})
        self.popup.add_handlers({curses.KEY_F2: self.parent.nextForm})
        self.popup.add_handlers({"^D": self.close})
        self.popup.beforeEditing = self.beforeEditing
        self.popup.afterEditing = self.afterEditing

        self.user = self.popup.add(npyscreen.TitleText, relx=3, rely=2, name="User:", value="admin", editable=0,
                                   field_width=self.width-15, begin_entry_at=11)
        self.status = self.popup.add(npyscreen.TitleText, relx=3, rely=3, name="Status:", value="",
                                     editable=0, field_width=self.width-17, begin_entry_at=11)
        self.ip = self.popup.add(npyscreen.TitleText, relx=3, rely=5, name="Address:", value="", editable=0,
                                 field_width=self.width-17, begin_entry_at=11)
        self.host = self.popup.add(npyscreen.TitleText, relx=3, rely=6, name="Host:", value="",
                                   editable=0, field_width=self.width-15, begin_entry_at=11)
        self.client = self.popup.add(npyscreen.TitleText, relx=3, rely=8, name="Client:", value="",
                                     editable=0, field_width=self.width-17, begin_entry_at=11)
        self.clientos = self.popup.add(npyscreen.FixedText, relx=14, rely=9, value="moo cow",
                                       editable=0, fwidth=self.width-17)
        self.login = self.popup.add(npyscreen.TitleText, relx=3, rely=10, name="Login Time:", value="",
                                    editable=0, field_width=self.width-22, begin_entry_at=14)

        self.idle = self.popup.add(npyscreen.TitleText, relx=3, rely=11, name="Idle Time:", value="",
                                   editable=0, field_width=self.width-21, begin_entry_at=14)
        self.transfer = []
        self.transfer.append(transferIndicator(self.popup, 3, 13, self.width-10))
        self.transfer[0].build()
        self.transfer[0].hide()
        self.transfer.append(transferIndicator(self.popup, 3, 15, self.width-10))
        self.transfer[1].build()
        self.transfer[1].hide()
        self.closebutton = self.popup.add(npyscreen.ButtonPress, relx=3, rely=self.height-3, name="Close")
        self.closebutton.whenPressed = self.close
        return self.popup

    def populate(self):
        userinfo = self.parent.librewired.getUserInfo(self.userid)
        if not userinfo:
            return 0
        self.user.value = userinfo['login']
        self.status.value = userinfo['status']
        self.ip.value = userinfo['ip']
        self.host.value = userinfo['host']
        version = parseVersionString(userinfo['client-version'])
        if type(version) is dict:
            self.client.value, self.clientos.value = formatVersion(version)
        else:
            self.client.value = version
            self.clientos = ''
        login = rewireFunctions.wiredTimeToTimestamp(userinfo['login-time'])
        self.login.value = rewireFunctions.formatTime(time() - login)
        idle = rewireFunctions.wiredTimeToTimestamp(userinfo['idle-time'])
        self.idle.value = rewireFunctions.formatTime(time() - idle)

        self.transfer[0].active = 0
        self.transfer[1].active = 0

        if len(userinfo['uploads']):
            display = 1
            if len(userinfo['uploads']) > 1 and not len(userinfo['downloads']):
                display = 2
            for i in range(0, display):
                upload = userinfo['uploads'][i]
                self.transfer[i].update("Upload:", basename(upload['path']), int(upload['size']),
                                        int(upload['transferred']), int(upload['speed']))
                self.transfer[i].display()
                self.transfer[i].active = 1
        else:
            display = 0

        if len(userinfo['downloads']):
            if len(userinfo['uploads']):
                offset = display
            else:
                display = 1
                offset = 0
            if len(userinfo['downloads']) > 1 and not len(userinfo['uploads']):
                display = 2
            for i in range(0, display):
                download = userinfo['downloads'][i]
                self.transfer[i+offset].update("Download:", basename(download['path']), int(download['size']),
                                               int(download['transferred']), int(download['speed']))
                self.transfer[i+offset].display()
                self.transfer[i+offset].active = 1

        for i in range(0, 2):
            if not self.transfer[i].active:
                self.transfer[i].hide()
        self.popup.display()
        if self.refreshtimer:
            self.refreshtimer = Timer(2, self.populate)
            self.refreshtimer.start()
        return

    def close(self, *args, **kwargs):
        if self.refreshtimer:
            self.refreshtimer.cancel()
            self.refreshtimer.join(2)
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)

    def beforeEditing(self):
        if not self.refreshtimer:
            self.refreshtimer = Timer(2, self.populate)
            self.refreshtimer.start()

    def afterEditing(self):
        if self.refreshtimer:
            self.refreshtimer.cancel()
            self.refreshtimer.join(1)
            self.refreshtimer = 0


class transferIndicator():
    def __init__(self, parent, relx, rely, width, label="Transfer:", filename="Null"):
        self.parent = parent
        self.relx = relx
        self.rely = rely
        self.width = width
        self.label = label
        self.filename = filename
        self.speed = 0

    def build(self):
        self.label = self.parent.add(npyscreen.TitleText, relx=self.relx, rely=self.rely,
                                     name=self.label, value=self.filename, editable=0, field_width=self.width-6,
                                     begin_entry_at=len(self.label)+3)
        self.slider = self.parent.add(npyscreen.Slider, relx=self.relx, rely=self.rely+1,
                                      out_of=31.4, value=10.2, max_width=self.width-10, editable=0)
        self.speed = self.parent.add(npyscreen.FixedText, relx=self.width-7, rely=self.rely+1,
                                     value=" @"+format_size(self.speed), editable=0)

    def display(self):
        self.label.hidden = 0
        self.label.display()
        self.slider.hidden = 0
        self.slider.display()
        self.speed.hidden = 0
        self.speed.display()

    def hide(self):
        self.label.hidden = 1
        self.label.display()
        self.slider.hidden = 1
        self.slider.display()
        self.speed.hidden = 1
        self.speed.display()

    def update(self, trtype, filename, total, progress, speed):
        try:
            if self.label.label_widget.value != trtype:
                self.label.label_widget.value = trtype
                self.label.label_widget.update()
            if filename != self.label.value:
                self.label.value = filename
                self.label.update()
            progress, total = format_size_numeric(progress, total)
            if self.slider.out_of != total or self.slider.value != progress:
                self.slider.out_of = total
                self.slider.value = progress
                self.slider.update()
            if self.speed.value != " @"+format_size(speed)+"/s":
                self.speed.value = " @"+format_size(speed)+"/s"
                self.speed.update()
            return
        except ValueError:
            return


def format_size(size):
    for x in [' B', ' kB', ' MB', ' GB']:
        if size < 1024.0 and size > -1024.0:
            size = "%3.1f%s" % (size, x)
            return size
        size /= 1024.0
    return "%3.1f%s" % (size, ' TB')


def format_size_numeric(progress, size):
    for x in range(0, 3):
        if size < 1024.0 and size > -1024.0:
            return (round(progress, 2), round(size, 2))
        size /= 1024.0
        progress /= 1024.0
    return (round(progress, 2), round(size, 2))


def parseVersionString(versionString):
    from re import compile
    try:
        parsed = {}
        if not "/" in versionString:
            return versionString  # malformed
        app = versionString.split("/")
        parsed['app'] = app[0]
        parts = app[1:]
        regex = compile("\(([^\)]*)\)")
        parts = regex.split(parts[0])
        parsed['version'] = parts[0]
        parsed['os'] = parts[1].split("; ")
        return parsed
    except:
        return versionString


def formatVersion(parsed):
    try:
        app = parsed['app'] + " "
        app += "(" + parsed['version'].strip() + ") on"
        os = "" + parsed['os'][0] + " " + parsed['os'][1] + " " + parsed['os'][2]
        return (app, os)
    except:
        if 'app' in parsed:
            return (parsed['app'], '')
        return 0
