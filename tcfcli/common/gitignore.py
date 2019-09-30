import os
import fnmatch as _fnmatch
import re as _re

try:
    range
except NameError:
    range = xrange

MATCH_IGNORE = 'ignore'  #: Ignore the file.
MATCH_INCLUDE = 'include'  #: Include the file.
MATCH_DEFAULT = 'default'  #: Default to include, but something else may override this.


class Pattern(object):

    def __init__(self, pattern, invert=False):
        self.parts = pattern.split('/')
        self.invert = invert
        self.is_abs = not self.parts[0]
        self.has_slash = len(self.parts) != 1
        self.dir_only = not self.parts[-1]

    def __str__(self):
        prefix = '!' if self.invert else ''
        return prefix + '/'.join(self.parts)

    def __repr__(self):
        return '<Pattern {0!r} invert={1} is_abs={2} has_slash={3} dir_only={4}>'.format(
            str(self), self.invert, self.is_abs, self.has_slash, self.dir_only)

    def match(self, filename):
        filename = os.path.normpath(filename).replace(os.sep, '/')
        # Does not take #Pattern.invert into account.
        if isinstance(filename, str):
            filename = filename.split('/')
        if len(filename) < len(self.parts):
            return False
        # print("match()", repr(self), filename, self.parts)
        fnmatch = _fnmatch.fnmatch
        if self.is_abs:
            for patpart, fpart in zip(self.parts, filename):
                if not fnmatch(fpart, patpart):
                    return False
            return True
        else:
            for i in range(len(filename) - len(self.parts) + 1):
                for patpart, fpart in zip(self.parts, filename[i:]):
                    if not fnmatch(fpart, patpart):
                        break
                else:
                    return True
            return False


class IgnoreList(object):

    def __init__(self, root=None, patterns=None):
        if root is not None:
            root = os.path.normpath(os.path.abspath(root))
        self.root = root
        self.patterns = patterns or []

    def __repr__(self):
        return '<IgnoreList root={0!r} patterns({1})>'.format(
            self.root, len(self.patterns))

    def __bool__(self):
        return bool(self.patterns)

    __nonzero__ = __bool__

    def parse(self, lines):
        """
        Parses the `.gitignore` file represented by the *lines*.
        """

        if isinstance(lines, str):
            lines = lines.split('\n')
        sub = _re.sub
        for line in lines:
            if line.endswith('\n'):
                line = line[:-1]
            line = line.lstrip()
            if not line.startswith('#'):
                invert = False
                if line.startswith('!'):
                    line = line[1:]
                    invert = True
                while line.endswith(' ') and line[-2:] != '\ ':
                    line = line[:-1]
                line = sub(r'\\([!# ])', r'\1', line)
                if '/' in line and not line.startswith('/'):
                    # Patterns with a slash can only be matched absolute.
                    line = '/' + line
                self.patterns.append(Pattern(line, invert))

    def convert_path(self, path):
        if os.path.isabs(path):
            if self.root is None:
                raise ValueError('IgnoreList.root not set, can not handle absolute paths')
            path = os.path.relpath(path, self.root)
        path = os.path.normpath(path)
        if path.startswith(os.pardir + os.sep) or path.startswith(os.curdir + os.sep):
            raise ValueError("path ({0!r}) is not under the IgnoreList.root directory ({1!r})".format(path, self.root))
        if os.sep != '/':
            path = path.replace(os.sep, '/')
        return '/' + path

    def match(self, filename, isdir=False):
        """
        Match the specified *filename*. If *isdir* is False, directory-only
        patterns will be ignored.

        Returns one of

        - #MATCH_DEFAULT
        - #MATCH_IGNORE
        - #MATCH_INCLUDE
        """

        fnmatch = _fnmatch.fnmatch
        ignored = False
        filename = self.convert_path(filename)
        basename = os.path.basename(filename)

        for pattern in self.patterns:
            if pattern.dir_only and not isdir:
                continue
            if (not ignored or pattern.invert) and pattern.match(filename):
                if pattern.invert:  # This file is definitely NOT ignored, no matter what other patterns match
                    return MATCH_INCLUDE
                ignored = True
        if ignored:
            return MATCH_IGNORE
        else:
            return MATCH_DEFAULT

    def is_ignored(self, filename, isdir=False):
        """
        Matches and returns #True if the file/directory should be ignored.
        """

        return self.match(filename, isdir) == MATCH_IGNORE
