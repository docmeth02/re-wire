import npyscreen
import curses
from os import path, listdir


class fileview():
    def __init__(self, parent, formid):
        self.parent = parent
        self.formid = formid
        self.max_x = self.parent.max_x
        self.max_y = self.parent.max_y

    def build(self):
        self.popup = npyscreen.FormBaseNew(name="Files: @%s" % self.parent.host,
                                           framed=True, relx=0, rely=0, lines=self.max_y - 3,
                                           columns=self.max_x - 2)
        self.popup.formid = self.formid
        self.popup.show_atx = 1
        self.popup.show_aty = 1
        half = int((self.max_x-2)/2)

        self.remoteview = remotefilebrowser(self.popup, self.parent.librewired, "/", 1, 2, half-1, self.max_y-18)
        self.remoteview.actionSelected = self.remoteActionSelected

        self.localview = localfilebrowser(self.popup, path.abspath(self.parent.homepath),
                                          half, 2, half-3, self.max_y-18, 'CAUTION')
        self.localview.actionSelected = self.localActionSelected

        self.closebutton = self.popup.add(npyscreen.ButtonPress, relx=2, rely=self.max_y-6, name="Close")
        self.closebutton.whenPressed = self.close
        self.popup.add_handlers({curses.KEY_F1: self.parent.prevForm})
        self.popup.add_handlers({curses.KEY_F2: self.parent.nextForm})
        self.popup.add_handlers({curses.KEY_F3: self.parent.openMessageView})
        self.popup.add_handlers({curses.KEY_F4: self.parent.openNewsView})
        self.popup.add_handlers({curses.KEY_F5: self.close})
        return self.popup

    def close(self, *args, **kwargs):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)
        self.parent.fileview = 0

    def localActionSelected(self, sourcepath, pathtype, action):
        if 'Upload' in action:
            target = self.remoteview.path
            confirm = npyscreen.notify_ok_cancel("Upload %s to folder %s?" %
                                                 (sourcepath, target), "Start upload")
            if not confirm:
                return 0
            transfer = self.parent.librewired.upload(sourcepath, target)
            self.parent.transfers.append(transfer)
            return 1
        #npyscreen.notify_confirm("Local: %s - %s - %s" % (path, pathtype, action))

    def remoteActionSelected(self, sourcepath, pathtype, action):
        if 'Download' in action:
            target = self.localview.path
            confirm = npyscreen.notify_ok_cancel("Download %s to local folder %s?" %
                                                 (sourcepath, target), "Start download")
            if not confirm:
                return 0
            transfer = self.parent.librewired.download(target, sourcepath)
            self.parent.transfers.append(transfer)
            return 1


class filebrowser(object):
    def __init__(self, parentform, path, relx, rely, width, height, color):
        self.parent = parentform
        self.path = path
        self.max_x = self.parent.max_x
        self.max_y = self.parent.max_y
        self.relx = relx
        self.rely = rely
        self.width = width
        self.height = height
        self.color = color
        self.dirtype = 0
        self.parentfolder = '* Parent Folder *'
        self.parentpos = 0
        self.fileoptions = []
        self.diroptions = []
        self.items = []

        ###
        self.label = self.parent.add_widget(npyscreen.FixedText, relx=self.relx, rely=self.rely, editable=0,
                                            value="", max_width=self.width, color="CURSOR")
        self.select = self.parent.add_widget(npyscreen.MultiLineAction, relx=self.relx, rely=self.rely+1,
                                             slow_scroll=True, max_height=self.height - 9, height=self.height-9,
                                             values=self.items, max_width=self.width, color=self.color,
                                             widgets_inherit_color=True)

        self.select.add_handlers({curses.ascii.SP: self.itemSelected})
        self.select.actionHighlighted = self.itemHighlighted

        self.populate()
        self.select.display()

    def populate(self):
        pass

    def itemSelected(self, *args):
        self.select.value = self.select.values[self.select.cursor_line]
        selection = self.select.value
        if selection == self.parentfolder:
            self.itemHighlighted(selection)
            return
        pathtype = -1
        isdir, dirtype = self.selectionIsPath(selection)
        if isdir:
            selection = isdir
            pathtype = dirtype
        action = self.popupmenu(path.join(self.path, selection), pathtype)
        if action:
            self.actionSelected(path.join(self.path, selection), pathtype, action)
        return 1

    def itemHighlighted(self, selection, *args):
        if selection == self.parentfolder:
            self.path = path.split(self.path)[0]
            if self.parentpos:
                self.select.cursor_line = self.parentpos  # restore position
                self.parentpos = 0
            self.populate()
            return 1
        isdir, dirtype = self.selectionIsPath(selection)
        if isdir:
            self.dirtype = dirtype
            self.path = path.join(self.path, isdir)
            self.parentpos = self.select.cursor_line  # store position for parent folder
            self.select.cursor_line = 0
            self.populate()
            return 1
        ## file
        action = self.popupmenu(path.join(self.path, selection), "FILE")
        if action:
            self.actionSelected(path.join(self.path, selection), 'FILE', action)
        return 1

    def selectionIsPath(self, selection):
        for atype, asep in self.foldertypes.items():
            asep = asep % ""
            if asep[:1] in selection[:1] and asep[-1] in selection[-1]:
                return (selection[1:-1], atype)
        return (0, 0)

    def actionSelected(self, path, pathtype, action):
        pass

    def popupmenu(self, path, pathtype, options=False):
        if not options:
            options = []
            if pathtype < 0:
                if len(self.fileoptions):
                    options += (self.fileoptions)
            else:
                if len(self.diroptions):
                    options += (self.diroptions)
        options.insert(0, 'Cancel')
        height = len(options)+4
        if height <= 5:
            height = 6
        menu = npyscreen.Popup(name="Select action:", framed=True, lines=height, columns=25)
        menu.show_atx = self.relx + 1
        menu.show_aty = (self.rely + 3) + (self.select.cursor_line - self.select.start_display_at)
        if menu.show_aty >= self.max_y - 10:
            menu.show_aty = self.max_y - 10
        selector = menu.add_widget(npyscreen.MultiLine, values=options, value=None, color="CURSOR",
                                   widgets_inherit_color=True,  slow_scroll=True, return_exit=True,
                                   select_exit=True, width=20)
        menu.display()
        selector.edit()
        if selector.value:
            return options[selector.value]
        return 0


class localfilebrowser(filebrowser):
    def __init__(self, parentform, path, relx, rely, width, height, color="NO_EDIT"):
        self.foldertypes = {0: "[%s]"}
        super(localfilebrowser, self).__init__(parentform, path, relx, rely, width, height, color)
        self.fileoptions = ['Upload']
        self.diroptions = ['Upload']

    def populate(self):
        self.items = []
        if path.exists(self.path):
            for aitem in sorted(listdir(self.path), key=str.lower):
                if "." in aitem[:1]:
                    continue
                if path.isdir(path.join(self.path, aitem)):
                    self.items.append(self.foldertypes[0] % aitem)
                    continue
                self.items.append(aitem)
            self.select.values = self.items
        if self.path != "/":
            self.items.insert(0, self.parentfolder)
        self.label.value = "Local: %s" % display_path(self.path, self.width-11)
        self.label.update()
        self.select.display()

    def actionSelected(self, path, pathtype, action):
        pass


class remotefilebrowser(filebrowser):
    def __init__(self, parentform, librewired, path, relx, rely, width, height, color="NO_EDIT"):
        self.librewired = librewired
        self.foldertypes = {1: '[%s]', 2: '(%s)', 3: '<%s>'}
        super(remotefilebrowser, self).__init__(parentform, path, relx, rely, width, height, color)
        self.fileoptions = ['Download', 'Info', 'Delete']
        self.diroptions = self.fileoptions + ['Create Folder']

    def populate(self):
        self.items = []
        if not self.librewired.loggedin:
            return 0
        result = self.librewired.listDirectory(self.path)
        if not type(result) is list:
            npyscreen.notify_confirm("Server failed to list %s" % self.path, "Server Error")
            return 0
        dirlist = sorted(result, key=lambda x: x.path,  cmp=lambda x, y: cmp(x.lower(), y.lower()))
        for aitem in dirlist:
            if int(aitem.type) in range(1, len(self.foldertypes)+1):
                self.items.append(self.foldertypes[int(aitem.type)] % path.basename(aitem.path))
                continue
            self.items.append(path.basename(aitem.path))
        self.select.values = self.items
        if self.path != "/":
            self.items.insert(0, self.parentfolder)
        self.label.value = "Remote: %s" % display_path(self.path, self.width-11)
        self.label.update()
        self.select.display()

    def actionSelected(self, path, pathtype, action):
        pass


def display_path(apath, length):
    if len(apath) <= length:
        return apath
    apath = apath[len(apath) - length:]
    return "..%s" % apath
