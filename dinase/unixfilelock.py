# -*- coding: utf-8 -*-

import fcntl
import errno


class AlreadyLocked(IOError):
    pass


class ReleaseError(IOError):
    pass


class UnixFileLock(object):

    def __init__(self, lock_file):
        super(UnixFileLock, self).__init__()

        self.lock_file = lock_file
        self.__fd = open(self.lock_file, "wb")

    def acquire(self, blocking=False):
        op = fcntl.LOCK_EX

        if not blocking:
            op |= fcntl.LOCK_NB

        try:
            fcntl.flock(self.__fd, op)
        except IOError as e:
            if e.errno != errno.EAGAIN:
                raise

            raise AlreadyLocked()

    def release(self):
        fcntl.flock(self.__fd, fcntl.LOCK_UN)

        if self.is_locked():
            raise ReleaseError()

    def is_locked(self):
        try:
            fcntl.flock(self.__fd, fcntl.LOCK_EX)
        except IOError as e:
            if e.errno != errno.EAGAIN:
                raise

            fcntl.flock(self.__fd, fcntl.LOCK_UN)

            return True

        else:
            return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.release()
