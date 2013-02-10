from reusabletext import parse


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
        if node.tokens and node.tokens[0] == 'section':
            if 'fallacy' in metadata.get('conceptType', ()):
                node.formatID = 'fallacy'
            else:
                node.formatID = 'section'
        elif node.tokens and node.tokens[0] == ':question:':
            hide_children(node) # don't show children separately
            if 'multichoice' in childDict:
                node.formatID = 'multichoice-question'
            elif 'question' in childDict:
                node.formatID = 'multipart-question'
            else:
                node.formatID = 'question'
        elif node.tokens and node.tokens[0] in self.blockDict:
            node.formatID = self.blockDict[node.tokens[0]]
        elif node.tokens and node.tokens[0][1:-1] in self.formatDict:
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
            s = t.render(this=node, children=node.children,
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
        finally:
            self.close()
        

def make_title(title, level):
    sectionMarks = '-.+=_:'
    return title + '\n' + len(title) * sectionMarks[level]

def apply_walk(node, func):
    func(node)
    for c in node.children:
        apply_walk(c, func)
