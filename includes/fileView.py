import npyscreen
import curses
from includes import rewireFunctions
from os import path, listdir
from re import search
from time import strftime, localtime


class fileview():
    def __init__(self, parent, formid):
        self.parent = parent
        self.formid = formid
        self.librewired = self.parent.librewired
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

        remoteoptions = []
        if self.librewired.privileges['download']:
            remoteoptions.append('Download')
        if self.librewired.privileges['alterFiles']:
            remoteoptions.append('Rename')
            remoteoptions.append('Move')
        remoteoptions.append('Info')
        if self.librewired.privileges['deleteFiles']:
            remoteoptions.append('Delete')
        remotediroptions = remoteoptions
        if self.librewired.privileges['createFolders']:
            remotediroptions.append('Create Folder')

        self.remoteview = remotefilebrowser(self.popup, self.librewired, "/", 1, 2, half-1, self.max_y-18,
                                            remoteoptions, remotediroptions)
        self.remoteview.actionSelected = self.remoteActionSelected
        self.remoteview.rootSelected = self.remoteRootSelected
        self.remoteview.label.add_handlers({curses.ascii.SP: self.remoteRootSelected})
        self.remoteview.label.add_handlers({curses.ascii.NL: self.remoteRootSelected})
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
        self.popup.add_handlers({'^D': self.close})
        return self.popup

    def close(self, *args, **kwargs):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)
        self.parent.fileview = 0

    def localActionSelected(self, sourcepath, pathtype, action):
        if 'Upload' in action:
            if not self.librewired.privileges['uploadAnywhere'] and int(self.remoteview.dirtype) <= 1:
                npyscreen.notify_confirm("You are not allowed to upload to the remote directory",
                                         "Not allowed to upload")
                return 0
            target = self.remoteview.path
            confirm = npyscreen.notify_ok_cancel("Upload %s to folder %s?" %
                                                 (sourcepath, target), "Start upload")
            if not confirm:
                return 0
            transfer = self.librewired.upload(sourcepath, target)
            self.parent.transfers.append(transfer)
            return 1

    def remoteRootSelected(self, *args):
        options = []
        if self.librewired.privileges['download']:
            options.append('Download')
        options.append('Info')
        if self.librewired.privileges['createFolders']:
            options.append('Create Folder')
        action = self.remoteview.popupmenu(self.remoteview.path, 1, options, show_aty=self.remoteview.label.rely)
        if action:
            self.remoteActionSelected(self.remoteview.path, 1, action)
        return 0

    def remoteActionSelected(self, sourcepath, pathtype, action):
        if 'Download' in action:
            target = self.localview.path
            confirm = npyscreen.notify_ok_cancel("Download %s to local folder %s?" %
                                                 (sourcepath, target), "Start download")
            if not confirm:
                return 0
            transfer = self.librewired.download(target, sourcepath)
            self.parent.transfers.append(transfer)
        elif 'Delete' in action:
            if npyscreen.notify_ok_cancel("Are you sure you want to delete %s?\nThis action cannot be undone!"
                                          % sourcepath, "Delete"):
                if not self.librewired.delete(sourcepath):
                    npyscreen.notify_confirm("Server failed to delete %s" % sourcepath, "Server Error")
                    return 0
                self.remoteview.populate()
                return 1
            return 0

        elif 'Rename' in action:
            oldpath = sourcepath
            newpath = rewireFunctions.textDialog("Rename %s" % display_path(oldpath, 20), "New Name:", "Rename")
            if newpath:
                if not type(newpath) is str or search(r'[^A-Za-z0-9 _\-\.\\]', newpath):
                    npyscreen.notify_confirm("You need to enter a valid new filename!")
                    return 0
                newpath = path.join(path.dirname(oldpath), newpath)
                if not self.librewired.move(oldpath, newpath):
                    npyscreen.notify_confirm("Server failed to move %s to %s" % (oldpath, newpath), "Server Error")
                    return 0
                self.remoteview.populate()
                return 1
            return 0

        elif 'Create Folder' in action:
            options = ['Plain Folder']
            #npyscreen.notify_confirm(str(pathtype))
            if 'FILE' == str(pathtype):
                sourcepath = path.dirname(sourcepath)
            if self.librewired.privileges['alterFiles']:
                options.append('Drop Box')
                options.append('Uploads Folder')
            create = createFolder(display_path(sourcepath, 20), options)
            if create:
                foldertype = options[create[1]]
                if "Uploads Folder" == foldertype:
                    foldertype = 2
                elif "Drop Box" == foldertype:
                    foldertype = 3
                else:
                    foldertype = 1
                result = self.librewired.createFolder(path.join(sourcepath, create[0]), foldertype)
                if result:
                    self.remoteview.populate()
                    return 1
                npyscreen.notify_confirm("Server failed to create Folder!", "Server Error")
            return 0
        elif 'Info' in action:
            info = self.librewired.stat(sourcepath)
            if not info:
                npyscreen.notify_confirm("Server failed to deliver Info", "Server Error")
                return 0
            infopopup = fileInfo(self, info)
        elif 'Move' in action:
            select = dirpopup(self)
            select.build()
            domove = select.edit()
            if domove:
                if select.value:
                    name = path.basename(sourcepath)
                    target = path.join(select.value, name)
                    if sourcepath == target:
                        npyscreen.notify_confirm("%s and %s are the same path" % (sourcepath, target), "Unable to move")
                        return 0
                    if path.commonprefix([sourcepath, target]) == sourcepath:
                        npyscreen.notify_confirm("Can't move %s into a subdir of itself" % sourcepath, "Unable to move")
                        return 0
                    confirm = npyscreen.notify_ok_cancel("Move %s to %s" % (sourcepath, target), "Confirm move")
                    if not confirm:
                        return 0
                    result = self.librewired.move(sourcepath, target)
                    if not result:
                        npyscreen.notify_confirm("Failed to move %s" % sourcepath, "Server Error")
                        return 0
                    self.remoteview.populate()
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
        self.dirtype = 1
        self.parentfolder = '* Parent Folder *'
        self.parentpos = 0
        self.pathtree = {}
        self.fileoptions = []
        self.diroptions = []
        self.items = []

        ###
        self.label = self.parent.add_widget(npyscreen.FixedText, relx=self.relx, rely=self.rely, editable=0,
                                            value="", max_width=self.width, color="CURSOR")
        self.label.path = 0
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

    def rootSelected(self, *args):
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
            if self.path in self.pathtree:
                del(self.pathtree[self.path])
            self.path = path.split(self.path)[0]
            self.dirtype = 1
            if self.path in self.pathtree:
                self.dirtype = self.pathtree[self.path]
            if self.parentpos:
                self.select.cursor_line = self.parentpos  # restore position
                self.parentpos = 0
            self.populate()
            return 1
        isdir, dirtype = self.selectionIsPath(selection)
        if isdir:
            self.dirtype = dirtype
            self.path = path.join(self.path, isdir)
            self.pathtree[self.path] = dirtype
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

    def popupmenu(self, path, pathtype, options=False, **kwargs):
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
        if 'show_aty' in kwargs:
            menu.show_aty = kwargs['show_aty']
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

    def rootSelected(self, *args):
        pass


class remotefilebrowser(filebrowser):
    def __init__(self, parentform, librewired, path, relx, rely, width, height,
                 fileoptions, diroptions, color="NO_EDIT"):
        self.librewired = librewired
        self.foldertypes = {1: '[%s]', 2: '(%s)', 3: '<%s>'}
        super(remotefilebrowser, self).__init__(parentform, path, relx, rely, width, height, color)
        self.fileoptions = fileoptions
        self.diroptions = diroptions
        self.label.editable = 1
        self.label.add_handlers({curses.ascii.SP: self.rootSelected})
        self.label.add_handlers({curses.ascii.NL: self.rootSelected})

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

    def rootSelected(self, *args):
        pass


class remotedirbrowser(remotefilebrowser):
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
            pass
        self.select.values = self.items
        if self.path != "/":
            self.items.insert(0, self.parentfolder)
        self.label.value = "Remote: %s" % display_path(self.path, self.width-11)
        self.label.update()
        self.select.display()


def createFolder(path, options=['Folder', 'Upload Folder', 'Dropbox']):
    foldertype = 0
    create = npyscreen.ActionPopup(name="Create Folder in %s" % path)
    create.on_ok = rewireFunctions.on_ok
    create.on_cancel = rewireFunctions.on_cancel
    text = create.add_widget(npyscreen.TitleText, name="Name:", value="", begin_entry_at=8, rely=2)
    if len(options) > 1:
        foldertype = create.add_widget(npyscreen.TitleSelectOne, name="Type:", values=options, value=0, rely=4)
    action = create.edit()
    if action:
        if not text.value or search(r'[^A-Za-z0-9 _\-\.\\]', text.value):
            npyscreen.notify_confirm("You need to enter a valid filename")
            return 0
        if not foldertype:
            return (text.value, 0)
        return (text.value, foldertype.value[0])
    return 0


def fileInfo(parent, info):
    form = npyscreen.ActionPopup(name=info.path, lines=20, columns=40)
    form.show_atx = int((parent.max_x-40)/2)
    show_aty = 2
    form.on_ok = rewireFunctions.on_ok
    form.on_cancel = rewireFunctions.on_cancel
    name = form.add_widget(npyscreen.TitleText, name="Name:", value=path.basename(info.path), begin_entry_at=10, rely=2,
                           editable=int(parent.librewired.privileges['alterFiles']))
    where = form.add_widget(npyscreen.TitleFixedText, name="Where:", value=path.dirname(info.path),
                            begin_entry_at=12, rely=4, editable=0)
    types = ['File', 'Folder', 'Upload Folder', 'Dropbox']
    objtype = form.add_widget(npyscreen.TitleFixedText, name="Type:", value=types[int(info.type)],
                              begin_entry_at=12, rely=6, editable=0)
    sizestring = "%s items" % info.size
    if not int(info.type):
        sizestring = rewireFunctions.format_size(int(info.size))
    size = form.add_widget(npyscreen.TitleFixedText, name="Size:", value=sizestring,
                           begin_entry_at=12, rely=8, editable=0)
    created = form.add_widget(npyscreen.TitleFixedText, name="Created:",
                              value=str(strftime('%Y/%m/%d %H:%M:%S',
                                                 localtime(int(rewireFunctions.wiredTimeToTimestamp(info.created))))),
                              begin_entry_at=12, rely=10, editable=0)
    modified = form.add_widget(npyscreen.TitleFixedText, name="Modified:",
                               value=str(strftime('%Y/%m/%d %H:%M:%S',
                                                  localtime(int(rewireFunctions.wiredTimeToTimestamp(info.modified))))),
                               begin_entry_at=12, rely=11, editable=0)
    if not int(info.type):
        kind = 0
        cheksum = form.add_widget(npyscreen.TitleFixedText, name="Checksum:",
                                  value=str(info.checksum), begin_entry_at=12, rely=13, editable=0)
    if int(info.type) in range(1, 4):
        foldertype = ['Folder', 'Upload Folder', 'Dropbox']
        kind = form.add_widget(npyscreen.TitleSelectOne, name="Kind:", values=foldertype, value=int(info.type)-1,
                               rely=13, max_height=2, editable=int(parent.librewired.privileges['alterFiles']))
    commentlabel = form.add_widget(npyscreen.FixedText, value="Comment:", rely=15, editable=0)
    if not info.comment:
        info.comment = ""
    comment = form.add_widget(npyscreen.MultiLineEdit, name="Comment:", value=str(info.comment), relx=14,
                              rely=15, max_height=2, max_width=23,
                              editable=int(parent.librewired.privileges['alterFiles']))
    form.editw = 8
    if info.path == '/':
        name.value = '/'
        name.editable = 0
        kind.editable = 0

    action = form.edit()
    if action:
        if name.value != path.basename(info.path):
            if parent.librewired.privileges['alterFiles']:
                newpath = path.join(path.dirname(info.path), name.value)
                confirm = npyscreen.notify_ok_cancel("Rename %s to %s?" % (info.path, newpath))
                if confirm:
                    if not parent.librewired.move(info.path, newpath):
                        npyscreen.notify_confirm("Server failed to rename file", "Server Error")
                    else:
                        info.path = newpath
                        parent.remoteview.populate()
        if kind:
            if int(kind.value[0] + 1) != int(info.type):
                if parent.librewired.privileges['alterFiles']:
                    newtype = int(kind.value[0] + 1)
                    if not parent.librewired.changeType(info.path, newtype):
                        npyscreen.notify_confirm("Server failed to change folder Type", "Server Error")
                    else:
                        info.type = newtype
                        parent.remoteview.populate()

        if comment.value != info.comment:
            if parent.librewired.privileges['alterFiles']:
                if not parent.librewired.changeComment(info.path, str(comment.value)):
                    npyscreen.notify_confirm("Server failed to apply new comment", "Server Error")
                else:
                    info.comment = str(comment.value)
    return 0


class dirpopup():
    def __init__(self, parent):
        self.parent = parent
        self.name = "Select destination folder:"

    def build(self):
        self.form = npyscreen.ActionPopup(name=self.name, lines=20, columns=40)
        self.form.show_atx = int((self.parent.max_x-40)/2)
        self.form.show_aty = 2
        self.form.on_ok = self.on_ok
        self.form.on_cancel = rewireFunctions.on_cancel
        self.remoteview = remotedirbrowser(self.form, self.parent.librewired, "/", 1, 2, 35, 18, [], ['Select'])
        self.remoteview.actionSelected = self.folderSelected
        self.value = 0

    def edit(self):
        action = self.form.edit()
        return action

    def on_ok(self):
        dirpath, pathtype = self.remoteview.selectionIsPath(self.remoteview.items[self.remoteview.select.cursor_line])
        if dirpath:
            self.value = path.join(self.remoteview.path, dirpath)
            return 1
        return 0

    def folderSelected(self, sourcepath, pathtype, action):
        #npyscreen.notify_confirm(str("%s %s %s" % (sourcepath, pathtype, action)))
        if 'Select' in action:
            self.form.ok_button.value = 1
            self.value = sourcepath
            self.form.editing = 0
            self.form.exit_editing()
        return


def display_path(apath, length):
    if len(apath) <= length:
        return apath
    apath = apath[len(apath) - length:]
    return "..%s" % apath
