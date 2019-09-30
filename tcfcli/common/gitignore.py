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
    """
    Represents a single pattern in a `.gitignore` file.

    # Attributes
  
    parts (list of str): The parts of the pattern split by `/`. Joining
      the parts using this separator gives the full pattern again.
    invert (bool): True if the pattern explicitly *includes* the matched
      files rather than excluding them.
    is_abs (bool): True if the pattern is absolute (and thus only matches the
      root project directory).
    has_slash (bool): True if there is at least one slash in the pattern.
    dir_onl (bool): True if this pattern matches only directories (that is
      when the pattern ends with a slash).
    """

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
    """
    A collection of the patterns in a `.gitignore` file. Must be initialized
    with the path to the root directory of the repository to properly match
    absolute paths in the patterns.
    """

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


class IgnoreListCollection(list):
    """
    Represents a collection of #IgnoreList#s. Used to combine `.gitignore` files
    from multiple sources (see #gitignore.parse()).
    """

    def parse(self, lines, root):
        """
        Shortcut for #IgnoreList.parse() and #IgnoreListCollection.append().
        """

        lst = IgnoreList(root)
        lst.parse(lines)
        self.append(lst)

    def match(self, filename, isdir=False):
        """
        Match all the #IgnoreList#s` in this collection. Returns one of

        - #MATCH_DEFAULT
        - #MATCH_IGNORE
        - #MATCH_INCLUDE
        """

        for lst in self:
            result = lst.match(filename, isdir)
            if result != MATCH_DEFAULT:
                return result
        return MATCH_DEFAULT

    def is_ignored(self, filename, isdir=False):
        """
        Matches and returns #True if the file/directory should be ignored.
        """

        return self.match(filename, isdir) == MATCH_IGNORE


def parse(ignore_file='.gitignore', git_dir='.git', additional_files=(),
          global_=True, root_dir=None, defaults=True):
    """
    Collects a list of all ignore patterns configured in a local Git repository
    as specified in the Git documentation. See
    https://git-scm.com/docs/gitignore#_description

    The returned #IgnoreListCollection is guaranteed to contain at least one
    #IgnoreList with #IgnoreList.root pointing to the specified *root_dir* (which
    defaults to the parent directory of *git_dir*) as the first element.
    """

    result = IgnoreListCollection()

    if root_dir is None:
        if git_dir is None:
            raise ValueError("root_dir or git_dir must be specified")
        root_dir = os.path.dirname(os.path.abspath(git_dir))

    def parse(filename, root=None):
        if os.path.isfile(filename):
            if root is None:
                root = os.path.dirname(os.path.abspath(filename))
            with open(filename) as fp:
                result.parse(fp, root)

    result.append(IgnoreList(root_dir))
    if ignore_file is not None:
        parse(ignore_file)
    for filename in additional_files:
        parse(filename)
    if git_dir is not None:
        parse(os.path.join(git_dir, 'info', 'exclude'), root_dir)
    if global_:
        # TODO: Read the core.excludeFiles configuration value.
        parse(os.path.expanduser('~/.gitignore'), root_dir)
    if defaults:
        result.append(get_defaults(root_dir))
    return result


def get_defaults(root):
    """
    Returns a default #IgnoreList which excludes common SCM files and directories.
    """

    defaults = IgnoreList(root)
    defaults.parse([
        '.DS_Store',
        '/.git',
        '/.svn',
        '/.hg'
    ])
    return defaults


def walk(patterns, dirname):
    """
    Like #os.walk(), but filters the files and directories that are excluded by
    the specified *patterns*.

    # Arguments
    patterns (IgnoreList, IgnoreListCollection): Can also be any object that
      implements the #IgnoreList.match() interface.
    dirname (str): The directory to walk.
    """

    join = os.path.join
    for root, dirs, files in os.walk(dirname, topdown=True):
        dirs[:] = [d for d in dirs if patterns.match(join(root, d), True) != MATCH_IGNORE]
        files[:] = [f for f in files if patterns.match(join(root, f), False) != MATCH_IGNORE]
        yield root, dirs, files
