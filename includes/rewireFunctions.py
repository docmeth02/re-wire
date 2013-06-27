from ConfigParser import ConfigParser
from time import time, altzone, timezone, mktime, daylight
from datetime import datetime, timedelta
from os import path, environ, pathsep, devnull, getcwd
from subprocess import call
import npyscreen


def load_config(fullpath, filename=False):
    config = ConfigParser()
    conffile = 'rewire.conf'
    if filename:
        conffile = filename
    if not path.exists(path.join(fullpath, conffile)):
        ## Create default config file
        config.add_section("settings")
        config.set("settings", 'timestampchat', '1')
        config.set("settings", 'timeformat', '[%H:%M]')
        config.add_section("defaults")
        config.set("defaults", 'server', 're-wired.info')
        config.set("defaults", 'port', '2000')
        config.set("defaults", 'user', 'guest')
        config.set("defaults", 'password', '')
        config.set("defaults", 'pwhash', '')
        config.set("defaults", 'autoreconnect', '0')
        config.set("defaults", 'nick', 're:wire')
        config.set("defaults", 'status', 'Another re:wire client')
        config.set("defaults", 'icon', 'data/default.png')
        config.set("defaults", 'connectonstart', '0')

        with open(path.join(fullpath, conffile), 'w') as newfile:
            config.write(newfile)
    else:
        try:
            config.read(path.join(fullpath, conffile))
        except Exception as e:
            pass
    config.set("DEFAULT", 'timestampchat', '1')
    config.set("DEFAULT", 'timeformat', '[%H:%M]')
    config.set("DEFAULT", 'server', 're-wired.info')
    config.set("DEFAULT", 'port', '2000')
    config.set("DEFAULT", 'user', 'guest')
    config.set("DEFAULT", 'password', '')
    config.set("DEFAULT", 'pwhash', '')
    config.set("DEFAULT", 'autoreconnect', '0')
    config.set("DEFAULT", 'nick', 're:wire')
    config.set("DEFAULT", 'status', 'Another re:wire client')
    config.set("DEFAULT", 'icon', 'data/default.png')
    config.set("DEFAULT", 'connectonstart', '0')
    return config


def on_ok():
    return 1


def on_cancel():
    return 0


def composeMessage(userid):
    reply = npyscreen.ActionPopup(name="Compose Message")
    reply.OK_BUTTON_TEXT = "Send"
    reply.on_ok = on_ok
    reply.on_cancel = on_cancel
    label = reply.add_widget(npyscreen.FixedText, value="Message text:", editable=0, rely=1)
    text = reply.add_widget(npyscreen.MultiLineEdit, name="Text:", value="", begin_entry_at=8, rely=2)
    action = reply.edit()
    if action and text.value:
        return text.value
    return 0


def textDialog(title, inputlabel="Enter text:", oklabel="OK"):
    form = npyscreen.ActionPopup(name=title)
    form.OK_BUTTON_TEXT = oklabel
    form.on_ok = on_ok
    form.on_cancel = on_cancel
    label = form.add_widget(npyscreen.FixedText, value=inputlabel, editable=0, rely=1)
    text = form.add_widget(npyscreen.MultiLineEdit, value="", begin_entry_at=8, rely=2)
    action = form.edit()
    if action and text.value:
        return text.value
    return action


def wiredTimeToTimestamp(timestring):
    if daylight:  # use offset including DST
        offset = altzone
    else:
        offset = timezone
    try:
        parsed = datetime.strptime(timestring[:-6], '%Y-%m-%dT%H:%M:%S')
        parsed -= timedelta(hours=int(timestring[-5:-3]), minutes=int(timestring[-2:]))*int(timestring[-6:-5]+'1')
        parsed -= timedelta(seconds=offset)
    except ValueError:
        return 0
    return mktime(parsed.timetuple())


def formatTime(seconds):
    days = int(seconds // (3600 * 24))
    hours = int((seconds // 3600) % 24)
    minutes = int((seconds // 60) % 60)
    seconds = int(seconds % 60)
    return "%s days, %s:%s:%s" % (days, str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2))


def checkssWiredImage(string):
    if "data:image" in string:
        if string.count(chr(3)) == 2:
            string = string[:string.find(chr(3))]
        if string.count(chr(128)):
            string = string.replace(chr(128), '')
    return string


def gitVersion(basepath):
    # parse git branch and commitid to server version string
    hasgit = 0
    # test for git command
    for dir in environ['PATH'].split(pathsep):
        if path.exists(path.join(dir, 'git')):
            try:
                call([path.join(dir, 'git')], stdout=open(devnull, "w"), stderr=open(devnull, "w"))
            except OSError, e:
                break
            hasgit = 1
    if hasgit:
        if path.exists(path.join(getcwd(), basepath, "git-version.sh")):
            # both git and our version script exist
            call([path.join(getcwd(), basepath, "git-version.sh")],
                 stdout=open(devnull, "w"), stderr=open(devnull, "w"))
    # check for version token and load it
    if path.exists(path.join(getcwd(), basepath, ".gitversion")):
        version = 0
        try:
            with open(path.join(getcwd(), basepath, ".gitversion"), 'r') as f:
                version = f.readline()
        except (IOError, OSError):
            return 0
        return version.strip()
    return 0
