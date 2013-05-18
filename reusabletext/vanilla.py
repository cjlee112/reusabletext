import parse
import os

def hide_children(node):
    for c in node.children:
        c.add_metadata_attrs(parse.PostprocDict)
        c.hide = True
        hide_children(c)

class Reformatter(object):
    def __init__(self, formatDict, blockDict={}):
        self.formatDict = formatDict
        self.blockDict = blockDict
        self.ifile = None

    def __call__(self, node):
        'mark node with appropriate format to use'
        try:
            metadata = node.metadata_dict()
        except AttributeError:
            return # nothing to do on the root
        childDict = node.child_dict()
        if not getattr(node, 'tokens', False):
            return
        elif node.tokens[0] == 'section':
            if 'fallacy' in metadata.get('conceptType', ()):
                node.formatID = 'fallacy'
            else:
                node.formatID = 'section'
        elif node.tokens[0] == ':question:':
            hide_children(node) # don't show children separately
            if 'multichoice' in childDict:
                node.formatID = 'multichoice-question'
            elif 'question' in childDict:
                node.formatID = 'multipart-question'
            else:
                node.formatID = 'question'
        elif node.tokens[0] in self.blockDict:
            node.formatID = self.blockDict[node.tokens[0]]
        elif node.tokens[0][1:-1] in self.formatDict:
            node.formatID = node.tokens[0][1:-1]

    def open(self, filepath):
        if self.ifile is not None:
            self.ifile.close()
        self.ifile = open(filepath, 'w')

    def render(self, node):
        if getattr(node, 'hide', False):
            return
        try:
            t = self.formatDict[node.formatID]
        except AttributeError:
            s = '\n'.join(getattr(node, 'text', []))
        else:
            node.add_metadata_attrs(parse.PostprocDict)
            try:
                title = node.title[0]
            except (AttributeError, IndexError):
                title = 'Untitled ' + node.formatID
            s = t.render(this=node, children=node.children, title=title,
                         indented=parse.indented, directive=parse.directive,
                         getattr=getattr, hasattr=hasattr, len=len, int=int,
                         make_title=make_title)
        self.ifile.write(s)

    def close(self):
        self.ifile.close()
        self.ifile = None

    def reformat(self, infile, outfile):
        tree = parse.parse_file(infile)
        apply_walk(tree, self) # mark nodes with appropriate formats
        self.open(outfile)
        try:
            apply_walk(tree, self.render)
            print >> self.ifile, '''

View `ReusableText Source <%s>`_
''' % os.path.basename(infile)
        finally:
            self.close()
        

def make_title(title, level=0):
    sectionMarks = '-.+=_:'
    return title + '\n' + len(title) * sectionMarks[level]

def apply_walk(node, func):
    func(node)
    for c in node.children:
        apply_walk(c, func)

def find_rst_files(topdir, suffix='.rst'):
    'get all .rst files in topdir'
    for dirpath, dirnames, filenames in os.walk(topdir):
        for fn in filenames:
            if fn.endswith(suffix):
                yield os.path.join(dirpath, fn)

def get_reformat_targets(topdir, excludeFile='exclude_reformat.txt'):
    'get all rust files to be reformatted'
    with open(os.path.join(topdir, excludeFile), 'rU') as ifile:
        excludeFiles = [s.strip() for s in ifile if s and not s.isspace()]
    l = []
    for path in find_rst_files(topdir):
        addThis = True
        for xf in excludeFiles: # check if path excluded
            if path.endswith(xf):
                addThis = False
                break
        if addThis:
            l.append(path)
    return l

def reformat_file(reformatter, target, tag='_vanilla'):
    'reformat foo.rst --> foo_vanilla.rst and return output path'
    pos = target.rindex('.') # find file suffix position
    output = target[:pos] + tag + target[pos:]
    reformatter.reformat(target, output)
    return output

def reformat_all(reformatFile, indexFile='index_vanilla.rst',
                 formatFile='vanilla_formats.rst'):
    'reformat all RuST in topdir, using specified templates'
    dirpath = os.path.dirname(reformatFile)
    with open(reformatFile, 'rU') as ifile:
        files = [os.path.join(dirpath, s.strip()) for s in ifile
                 if s and not s.isspace()]
    files.sort()
    formatDict = parse.read_formats(formatFile)
    reformatter = Reformatter(formatDict)
    with open(indexFile, 'w') as ifile:
        print >>ifile, '''
###################################################
Open Bioinformatics Teaching Consortium Release 0.1
###################################################

.. toctree::
   :maxdepth: 2

'''
        for target in files:
            s = reformat_file(reformatter, target)
            print >>ifile, '   ' + s[:s.rindex('.')]

def mark_levels(node, level=0):
    node.level = level
    for c in node.children:
        mark_levels(c, level + 1)


def render_docs(docs, reformatter, outfile, prologue=None):
    tree = parse.Document()
    tree.children = docs
    apply_walk(tree, reformatter)
    mark_levels(tree)
    reformatter.open(outfile)
    if prologue:
        reformatter.ifile.write(prologue)
    try:
        apply_walk(tree, reformatter.render)
    finally:
        reformatter.close()
