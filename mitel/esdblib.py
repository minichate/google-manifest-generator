"""This library is for the reading and writing of e-smith database records.
See http://smeserver.org for details."""

# TODO
# creating a new record, should automatically add to the db?
# record to dict?
# db to dict?

import logging
from logging.handlers import SysLogHandler
import re, os
if os.environ.has_key('ESDBLIB_LOG_DEBUG'):
    logging.basicConfig()
    log = logging.getLogger('esdblib')
    log.setLevel(logging.DEBUG)
else:
    # Default to logging to syslog.
    log = logging.getLogger('esdblib')
    log.setLevel(logging.INFO)
    syslog_handler = SysLogHandler(address='/dev/log')
    syslog_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s: [%(levelname)s] %(message)s')
    syslog_handler.setFormatter(formatter)
    log.addHandler(syslog_handler)

locking = True
try:
    import fcntl
except ImportError:
    log.warning("No fcntl module on this platform, locking not supported")
    locking = False

VERSION = '1.2'

class EsmithDbError(Exception):
    """Exceptions related to this API."""
    pass

class EsmithDbProperty(object):
    """Represents a single EsmithDb property and value. This class should only
    be accessed from an instance of EsmithDbRecord, which knows how to manage
    it properly."""

    def __init__(self, name, value):
        log.debug('in EsmithDbProperty.__init__()')
        log.debug("instantiating property - "
                  "name = %s, value = %s" % (name, value))
        self.name = name
        self.value = value
        self.dirty = False

    def __str__(self):
        return "%s=%s" % (self.name, self.value)

class EsmithDbRecord(object):
    """Represents a single EsmithDb record."""

    def __init__(self, db, key=None, type=''):
        log.debug('in EsmithDbRecord.__init__()')
        self.db = db
        self.key = key
        self.type = type
        self.props = {}
        self.dirty = False
        self.deletedProps = []

    def __str__(self):
        s = "%s=%s" % (self.key, self.type)
        for name, prop in self.props.items():
            s += "|%s|%s" % (name, prop.value)
        return s

    def __iter__(self):
        "Start iteration."
        allKeys = self.props.keys()
        allKeys.sort()
        for key in allKeys:
            yield self.props[key]

    def key_compare(r1, r2):
        if r1.key > r2.key:
            return 1
        elif r1.key < r2.key:
            return -1
        else: #r1.key == r2.key
            return 0
    def prettyPrint(self):
        s = "%s=%s" % (self.key, self.type)
        keys = self.props.keys()
        keys.sort()
        for key in keys:
            prop = self.props[key]
            s += "\n    " + str(prop)
        return s

    def merge(self, newer):
        """This method attempts to merge the newer record object with current,
        where newer is presumably a newer record object from the database."""
        log.debug('in EsmithDbRecord.merge() - key is %s' % self.key)

        for name, prop in newer.props.items():
            ours = self.props.get(prop.name, None)
            if ours and ours.dirty:
                log.debug("our %s prop is dirty, not clobbering" % ours.name)
            else:
                self.props[prop.name] = prop

        for delprop in self.deletedProps:
            if self.props.has_key(delprop.name):
                log.debug('deleting prop %s' % prop.name)
                del self.props[delprop.name]
        self.deletedProps = []

    def isDirty(self):
        """This method checks the dirty flags on all properties. If any of
        them are dirty it returns True, otherwise False. It also checks its
        internal dirty flag for the same, since the value can also be dirty
        independently of the properties."""
        if self.dirty:
            log.debug("EsmithDbRecord.isDirty - returning True for %s" % self.key)
            return True
        for name, prop in self.props.items():
            if prop.dirty:
                log.debug("EsmithDbRecord.isDirty - returning True for %s" % self.key)
                return True
        return False

    def clean(self):
        """This method sets all dirty flags related to this record to
        False."""
        log.debug('in EsmithDbRecord.clean()')
        self.dirty = False
        for name, prop in self.props.items():
            prop.dirty = False

    def getPropValue(self, name):
        """Return the value of the property referenced as a string, returning
        None if it does not exist."""
        log.debug('in EsmithDbRecord.getPropValue()')
        log.debug("asked to getPropValue %s" % name)
        prop = self.getProp(name)
        if prop == None:
            return None
        else:
            return prop.value

    def getProp(self, name):
        """Return the EsmithDbProperty object corresponding to the name
        passed, returning None if it does not exist."""
        log.debug('in EsmithDbRecord.getProp()')
        log.debug("asked to getProp %s" % name)
        return self.props.get(name, None)

    def delete(self, save=True):
        """Deletes the current record. By default, it saves immediately,
        unless save is False."""
        log.debug("in EsmithDbRecord.delete()")
        log.debug("save is %s" % save)

        self.db.delRecord(self)

    def delProp(self, name, save=True):
        log.debug('in EsmithDbRecord.delProp')
        log.debug('name is %s, save is %s' % (name, save))
        if self.props.has_key(name):
            log.info('%s: deleting property %s in record %s'
                % (self.db.path, name, self.key))
            prop = self.props[name]
            self.deletedProps.append(prop)
            del self.props[name]
            # Must be dirty or a record-level merge won't be done.
            self.dirty = True
        else:
            log.warn("asked to delProp %s, but we don't have one" % name)
            raise EsmithDbError, "Can't delProp %s, we don't have one" % name

        if save:
            self.db.lockReloadAndSave()

    def setProp(self, name, value, create=False, save=True):
        """Set the supplied property name to the value given. It will throw an
        EsmithDbError if the property does not already exist, unless the
        create parameter is True. If save is True, the db will be saved
        immediately."""
        log.debug('in EsmithDbRecord.setProp()')
        log.info("%s: record %s, prop %s <- %s"
            % (self.db.path, self.key, name, value))
        log.info("%s: OLD: %s" % (self.db.path, self))
        if not self.props.has_key(name):
            log.debug("property with key %s does not exist" % name)
            if create:
                log.debug("create is set - creating property")
                prop = EsmithDbProperty(name, value)
                self.addProp(prop, save=save)
                if save:
                    save=False # We just saved in addProp
            else:
                raise EsmithDbError, "property %s does not exist" % name
        else:
            log.debug("property exists already")
            self.props[name].value = value
            self.props[name].dirty = True
        log.info("%s: NEW: %s" % (self.db.path, self))

        if save:
            self.db.lockReloadAndSave()

    def setType(self, type, save=True, dirty=True):
        """Set the type of the current record, which also happens to be the
        value in a singleton record."""
        log.debug('in EsmithDbRecord.setType()')
        log.info("%s: record %s, type <- %s" % (self.db.path, self.key, type))
        log.info("%s: OLD: %s" % (self.db.path, self))
        self.type = type
        log.info("%s: NEW: %s" % (self.db.path, self))

        if dirty:
            self.dirty = True

        if save:
            self.db.lockReloadAndSave()

    def addProp(self, prop, clobber=False, save=True, dirty=True, loading=False):
        """Add the supplied property to the record. It will clobber any
        existing property by the same name if the clobber property is True.
        Otherwise it will raise an EsmithDbError exception. If save is True,
        the db will be saved immediately. By default, the dirty flag on the
        property is set to true, but this is overridden by the dirty 
        argument."""
        log.debug('in EsmithDbRecord.addProp()')
        log.debug("clobber is %s, save is %s" % (clobber, save))
        if not loading:
            log.info("%s: adding property %s to record %s"
                % (self.db.path, prop, self.key))
            log.info("%s: OLD: %s" % (self.db.path, self))
        if not clobber:
            if self.props.has_key(prop.name):
                raise EsmithDbError, "prop %s exists already" % prop.name
        self.props[prop.name] = prop
        if not loading:
            log.info("%s: NEW: %s" % (self.db.path, self))

        if dirty:
            log.debug("flagging property %s as dirty" % prop.name)
            prop.dirty = True

        if save:
            self.db.lockReloadAndSave()

    def parse(self, line):
        """This method is responsible for parsing a single line representing a
        EsmithDbRecord. Such a line looks like
           key=type|name1|prop1|name2|prop2
            While the | character is a delimiter, it may be used in names and
        values if backreferenced with a \ character. Still, this should be
        discouraged. 
            Singleton records are possible, with no properties. In such cases
        the type is the value of the record, and it may be the null string. If
        properties are present however, the type may not be blank."""
        log.debug('in EsmithDbRecord.parse()')
        self.key, rest = line.split('=', 1)
        log.debug("parsing line - key is %s, rest is %s" % (self.key, rest))
        if len(rest) > 0:
            pieces = re.split(r'(?<!\\)\|', rest)
            self.type = pieces[0]
            log.debug("type is %s" % self.type)
            pieces = pieces[1:]
            if len(pieces) % 2 != 0:
                raise EsmithDbError, "Odd number of name/value pairs on line: " + line
            names = pieces[::2]
            values = pieces[1::2]
            for i in range(len(names)):
                prop = EsmithDbProperty(names[i], values[i])
                self.addProp(prop,
                             clobber=True,
                             save=False,
                             dirty=False,
                             loading=True)

class EsmithDb(object):
    """This class represents an esmith database, taking the name of the db to
    open, or a full path to the file."""

    def __init__(self, name, dbdir="/home/e-smith/db"):
        """Pass in the name, in which case /home/e-smith/db will be used to
        prefix the name for the path, or supply an absolute or relative path
        to the file."""
        log.debug('in EsmithDb.__init__()')
        self.name = name.strip()
        self.path = ""
        self.semaphore_path = ""
        self.semaphore = None
        self.records = {}
        self.dirtyRecords = []
        self.deletedRecords = []
        self.reading = False
        self.writing = False
        self.dbfile = None

        if re.search(r'^\.?\.?/', self.name):
            log.debug("This is a path")
            dir, basename = os.path.split(self.name)
            self.path = self.name
            self.name = basename
            log.debug("path is %s, name is %s" % (self.path, self.name))

        else:
            log.debug("This is a name")
            if re.search(r'/', self.name):
                log.error("db names cannot contain / characters")
                raise EsmithDbError, "db names cannot contain / characters"

            self.path = dbdir + '/' + self.name
            log.debug("path is %s" % self.path)

        self.writable = os.access(self.path, os.W_OK)
        log.debug("instantiating db for %s" % self.path)
        self.semaphore_path = dbdir + '/.' + self.name + '.lock'

        self.readLockAndOpen()
        self.reload()
        self.unlockAndClose()

    def __iter__(self):
        "Start iteration."
        allKeys = self.records.keys()
        allKeys.sort()
        for key in allKeys:
            yield self.records[key]

    def delRecord(self, record, save=True):
        """This method deletes the record passed from the database, saving
        immediately by default unless save is False."""
        log.debug("in EsmithDb.delRecord() - record is %s" % record.key)
        self.deletedRecords.append(record)
        if self.records.has_key(record.key):
            log.info("%s: DEL: %s" % (self.path, record))
            del self.records[record.key]

        if save:
            self.lockReloadAndSave()

    def getRecord(self, key):
        """This method returns the EsmithDbRecord object corresponding to the
        key passed, returning None if it does not exist."""
        log.debug('in EsmithDb.getRecord()')
        log.debug("Returning record %s" % key)
        return self.records.get(key, None)

    def addRecord(self, record, clobber=False, save=True, loading=False):
        """This method adds a new record to the database. If clobber is False,
        then it will raise an exception if a record with the same key exists
        already. Otherwise it will clobber that record. By default it will
        save the db when the record is added, but not if the save parameter is
        False. If the loading parameter is True, then this method is being
        called while loading from the db file, and the method should log
        accordingly."""
        log.debug('in EsmithDb.addRecord()')
        if not loading:
            # We don't want to log while doing loading of the db file. Too
            # noisy.
            log.info("%s: ADD: %s" % (self.path, record))
        log.debug("clobber is %s, save is %s" % (clobber, save))
        if self.records.has_key(record.key):
            if clobber:
                self.records[record.key] = record
            else:
                raise EsmithDbError, "record %s already exists" % record.key
        else:
            self.records[record.key] = record

        if save:
            self.lockReloadAndSave()

    def reload(self):
        """This method loads the db into memory. If there is a db already
        loaded into memory, then it will attempt to merge with any changes
        that have been made in memory."""
        log.debug("in EsmithDb.reload()")
        needToUnlock = False
        if not self.reading and not self.writing:
            log.debug("the dbfile isn't open yet")
            self.readLockAndOpen()
            needToUnlock = True
        if self.records:
            if self.isDirty():
                log.debug("dirty records - move for merging")
                self.dirtyRecords = self.records
            self.records = {}

        skippat = re.compile(r'^$|^\s|^#')
        lineno = 0
        for line in self.dbfile.xreadlines():
            lineno += 1
            line = line.strip()
            log.debug("line %d is %s" % (lineno, line))
            if skippat.match(line):
                continue
            try:
                record = EsmithDbRecord(self)
                record.parse(line)
            except EsmithDbError:
                log.error("Parse error on line %d" % lineno)
                raise

            self.addRecord(record, save=False, loading=True)

        if lineno == 0:
            log.warn("reload: read nothing from the db file")
        if needToUnlock:
            log.debug("I locked the file. Need to unlock.")
            self.unlockAndClose()

    def merge(self):
        """This method merges the reloaded records with the dirty records in
        memory. If there are no dirty records, then this method is a noop."""
        log.debug('in EsmithDb.merge()')
        if not self.dirtyRecords:
            log.debug("Skipping merge, no dirty records")
        else:
            log.debug("Dirty records. Merging...")
            for dirtyKey, dirtyRecord in self.dirtyRecords.items():
                if dirtyRecord.isDirty():
                    log.debug("dirtyKey is %s" % dirtyKey)
                    if self.records.has_key(dirtyKey):
                        log.debug("Calling merge")
                        dirtyRecord.merge(self.records[dirtyKey])

                    self.records[dirtyKey] = dirtyRecord
                    dirtyRecord.clean()

            self.dirtyRecords = None

        for deletedRecord in self.deletedRecords:
            if self.records.has_key(deletedRecord.key):
                log.debug('deleting record %s' % deletedRecord.key)
                del self.records[deletedRecord.key]
            else:
                log.warn("deleted record %s is not known to us")
        self.deletedRecords = []

    def save(self, force=False):
        """This method performs an explicit save of the in-memory database to
        disk, overwriting whatever is currently in the file, unless the
        database is not dirty, in which case it is a noop. The exception to
        this is if the force argument is supplied, and is true. In this case
        it will write to the dbfile anyway. If called without a write lock on
        the dbfile, it will acquire one, and release the lock itself."""
        log.debug('in EsmithDb.save()')
        log.debug("Saving the database to disk")
        needToUnlock = False
        if not self.writing:
            log.debug("not writing yet, calling writeLockAndOpen")
            self.writeLockAndOpen()
            needToUnlock = True
        else:
            log.debug("file already open, seeking to beginning")
            self.dbfile.seek(0)

        count = 0
        keys = self.records.keys()
        keys.sort()
        for key in keys:
            record = self.records[key]
            log.debug("writing record %s to dbfile" % record.key)
            log.debug("%s" % record)
            self.dbfile.write("%s\n" % record)
            count += 1

        if count == 0:
            log.warn("save: wrote nothing to the db file")

        self.dbfile.truncate()

        if needToUnlock:
            log.debug("I locked the file. Need to unlock.")
            self.unlockAndClose()

    def readLockAndOpen(self):
        """This method attempts to acquire a shared lock on its database file.
        It manages the reading property, and will throw an exception if we
        already have a write lock. If we have a read lock already, this method
        is a noop. If successful, self.dbfile will be a file object, opened
        for reading."""
        log.debug('in EsmithDb.readLockAndOpen()')
        if self.writing:
            raise EsmithDbError, "readLockAndOpen: Already have a write lock"
        elif self.reading:
            log.debug("readLockAndOpen - we're already reading")
            return
        self.dbfile = open(self.path, "r")
        if locking and self.writable:
            self.semaphore = open(self.semaphore_path, 'w')
            fcntl.flock(self.semaphore, fcntl.LOCK_SH)
        self.reading = True
        self.dbfile.seek(0)

    def writeLockAndOpen(self):
        """This method attemps to acquire an exclusive lock on its database
        file. It manages the writing property, and will throw an exception
        if we already have a read lock. If we have a write lock already, this
        method is a noop. If successful, self.dbfile will be a file object,
        opened for writing."""
        log.debug('in EsmithDb.writeLockAndOpen()')
        if self.reading:
            raise EsmithDbError, "Already have a read lock"
        elif self.writing:
            log.debug("writeLockAndOpen - we're already writing")
            return
        self.dbfile = open(self.path, "r+")
        if locking and self.writable:
            self.semaphore = open(self.semaphore_path, 'w')
            fcntl.flock(self.semaphore, fcntl.LOCK_EX)
        self.writing = True
        self.dbfile.seek(0)

    def unlockAndClose(self):
        """This method releases any lock currently held on the dbfile, and
        closes the file."""
        log.debug('in EsmithDb.unlockAndClose()')
        if locking and self.writable:
            fcntl.flock(self.semaphore, fcntl.LOCK_UN)
            self.semaphore.close()
            self.semaphore = None
        self.dbfile.close()
        self.dbfile = None
        self.reading = False
        self.writing = False

    def isDirty(self):
        """This method searches the record list looking for dirty records. If
        any of them are dirty it returns True, False otherwise."""
        for key, record in self.records.items():
            if record.isDirty():
                return True
        return False

    def lockReloadAndSave(self):
        """This method locks the dbfile, reloads, merges, saves and
        unlocks."""
        log.debug('in EsmithDb.lockReloadAndSave()')
        self.writeLockAndOpen()
        self.reload()
        self.merge()
        self.save()
        self.unlockAndClose()

    def getAllByProp(self, propDict):
        """Return the list of EsmithDbRecord objects that match the given
        property value pairs. Return an empty list if no matching records found.
        Pass the property/value pairs as a dict."""
        log.debug('in EsmithDb.getAllByProp()')
        matching_list = []

        for record in self:
            log.debug("looping on record: %s" % record)
            for propname in propDict:
                if propname == 'type':
                    value = record.type
                else:
                    value = record.getPropValue(propname)
                if propDict[propname] != value:
                    break
            else:
                # Then we got through the for loop without breaking out. Which
                # means that we matched all passed props.
                matching_list.append(record)

        return matching_list


if __name__ == '__main__':
    import sys, os
    
    def usage():
        usage = '''\
Usage: %s <path to db> <operation>
    where operation is one of
    show <key>
    setprop <key> <name> <value>
    delprop <key> <name>
    delete <key>
'''
        sys.stderr.write(usage % sys.argv[0])
        sys.exit(1)

    nargs = len(sys.argv)
    if nargs < 3:
        usage()

    dbpath    = sys.argv[1]
    operation = sys.argv[2]

    loglevel = logging.INFO
    if os.environ.has_key('ESDB_QUIET'):
        loglevel = logging.WARNING
    if os.environ.has_key('ESDB_DEBUG'):
        loglevel = logging.DEBUG
    db = EsmithDb(dbpath, loglevel=loglevel)

    if operation == 'show':
        if nargs < 4:
            usage()
        key = sys.argv[3]
        rec = db.getRecord(key)
        if rec:
            print rec.prettyPrint()

    elif operation == 'setprop':
        if nargs < 6:
            usage()
        key      = sys.argv[3]
        propname = sys.argv[4]
        propval  = sys.argv[5]
        rec = db.getRecord(key)
        rec.setProp(propname, propval, create=True)

    elif operation == 'delprop':
        if nargs < 5:
            usage()
        key      = sys.argv[3]
        propname = sys.argv[4]
        rec = db.getRecord(key)
        rec.delProp(propname)

    elif operation == 'delete':
        if nargs < 4:
            usage()
        key = sys.argv[3]
        db.delRecord(db.getRecord(key))

    else:
        sys.stderr.write(usage % sys.argv[0])
        sys.exit(1)
