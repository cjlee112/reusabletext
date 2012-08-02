
from jinja2 import Template

sectionChars = '!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
minTitle = 4
defaultBlocks = (':question:', ':answer:', ':error:', ':intro:',
                 ':warning:', ':comment:', ':informal-definition:',
                 ':formal-definition:', ':derivation:',
                 '.. select::', ':format:'
                 )

def get_indent(i, rawtext, text):
    if text[i]:
        return rawtext[i].index(text[i][0])

def is_section_mark(i, rawtext, text):
    rawline = rawtext[i]
    if not rawline:
        return False
    line = text[i]
    c = rawline[0]
    if c in sectionChars and line == c * len(line) \
           and len(line) >= minTitle:
        return line

def is_section_overline(i, rawtext, text):
    if i + 2 < len(text) and is_section_mark(i, rawtext, text):
        l = [rawtext[j].rstrip() for j in range(i, i + 3)]
        if len(l[0]) >= len(l[1]) and l[0] == l[2]:
            return text[i + 1], 3, l[0][1]
        
def is_section_title(i, rawtext, text):
    if i + 2 < len(text):
        mark = is_section_mark(i + 1, rawtext, text)
        if mark and len(mark) >= len(text[i]) \
           and text[i] and rawtext[i][0] == text[i][0]:
            return text[i], 2, mark[0]

def is_section_start(i, rawtext, text):
    return is_section_overline(i, rawtext, text) \
           or is_section_title(i, rawtext, text)

def not_empty(text):
    for line in text:
        if line:
            return True

def generate_sections(rawtext, text, title=''):
    'generate section intervals as (start, stop, title, level) tuples'
    lastStart = i = 0
    n = len(rawtext)
    levels = []
    level = 0
    while i < n:
        section = is_section_start(i, rawtext, text)
        if section:
            if title or not_empty(text[lastStart:i]):
                yield [lastStart, i, title, level]
            title, step, mark = section
            i += step
            lastStart = i
            if mark not in levels:
                levels.append(mark)
            level = levels.index(mark)
        else:
            i += 1
    if title or not_empty(text[lastStart:]):
        yield [lastStart, len(text), title, level]

def get_section_forest(rawtext, text):
    'convert generate_sections() list into trees'
    stack = [[]]
    for t in generate_sections(rawtext, text):
        level = t[3]
        if level > len(stack):
            raise ValueError('section level too big!  Debug!')
        elif level == len(stack): # must expand the stack
            stack.append([t])
        else:
            for i in range(level + 1, len(stack)):
                subsections = stack.pop()
                stack[-1][-1].append(subsections)
            stack[-1].append(t)
    for i in range(1, len(stack)):
        subsections = stack.pop()
        stack[-1][-1].append(subsections)
    return stack[0] # top-level sections

def is_block_start(i, rawtext, text, blockTokens):
    tokens = text[i].split()
    if text[i].startswith('.. select::'):
        tokens = ['.. select::'] + text[i][11:].lstrip().split()
    if tokens and tokens[0] in blockTokens:
        start = i
        indent = get_indent(i, rawtext, text)
        i += 1
        subindent = None
        while i < len(text):
            subindent = get_indent(i, rawtext, text)
            if subindent is not None:
                break
            i += 1
        if subindent is not None and subindent > indent:
            i += 1
            while i < len(text):
                k = get_indent(i, rawtext, text)
                if k is not None and k < subindent:
                    break
                i += 1
        else: # no contents
            subindent = None
        return start, i, tokens, subindent

def generate_blocks(rawtext, text, blockTokens=defaultBlocks):
    'generate top-level blocks within a text'
    lastStart = i = 0
    n = len(rawtext)
    while i < n:
        block = is_block_start(i, rawtext, text, blockTokens)
        if block:
            yield block
            i = block[1]
        else:
            i += 1

def is_metadata(line):
    'matches any line beginning with :foobar: pattern'
    if line and line[0] == ':':
        token = line.split()[0]
        return token[-1] == ':' and len(token) > 2
            

def extract_metadata(rawtext, text, indent):
    'remove :foobar: metadata lines and de-indent rawtext'
    l = []
    metadata = []
    prefix = ' ' * indent
    for i, line in enumerate(text):
        if is_metadata(line):
            metadata.append(line)
        elif prefix and rawtext[i].startswith(prefix):
            l.append(rawtext[i][indent:])
        else:
            l.append(rawtext[i])
    return l, metadata

class Block(object):
    'a RUsT block, containing text and / or subblocks'
    def __init__(self, tokens, rawtext, text, indent=0,
                 blockTokens=defaultBlocks, **kwargs):
        self.tokens = tokens
        self.indent = indent
        self.__dict__.update(kwargs)
        if tokens[0] == '.. select::':
            self.children = parse_select(rawtext)
        elif rawtext:
            self.parse(rawtext, text, blockTokens)
        else:
            self.children = []
    def parse(self, rawtext, text, blockTokens):
        children = []
        stop = 0
        self.text = []
        self.metadata = []
        for start, stop, tokens, indent in generate_blocks(rawtext, text,
                                                           blockTokens):
            if not children and not_empty(text[:start]):
                self.text, self.metadata = \
                           extract_metadata(rawtext[:start], text[:start],
                                            self.indent)
            children.append(Block(tokens, rawtext[start + 1:stop],
                                  text[start + 1:stop], indent, blockTokens))
        if not_empty(text[stop:]):
            addtext, metadata = \
                     extract_metadata(rawtext[stop:], text[stop:], self.indent)
            self.text += addtext
            self.metadata += metadata
        self.children = children

    def metadata_dict(self):
        '''save metadata as dict values containing list of one
        or more values'''
        d = {}
        try:
            metadata = self.metadata
        except AttributeError:
            return d
        for line in metadata:
            attr = line.split(':')[1]
            v = line[len(attr) + 2:].lstrip()
            try:
                d[attr].append(v)
            except KeyError:
                d[attr] = [v]
        return d

    def child_dict(self, d=None):
        if d is None:
            d = {}
        for c in self.children:
            if c.tokens and getattr(c, 'text', False):
                attr = c.tokens[0][1:-1]
                v = ''.join(c.text)
                try:
                    d[attr].append(v)
                except KeyError:
                    d[attr] = [v]
        return d

    def add_metadata_attrs(self):
        'add metadata as attributes on this obj'
        self.__dict__.update(self.metadata_dict())
        self.__dict__.update(self.child_dict())

    def get_children(self, token):
        for c in self.children:
            if c.tokens and c.tokens[0] == token:
                yield c
    def walk(self):
        for c in self.children:
            for node in c.walk():
                yield node
        yield self

class Section(Block):
    'a ReST section, containing text, subblocks and / or subsections'
    def __init__(self, t, rawtext, text, **kwargs):
        start, stop, title, level = t[:4]
        Block.__init__(self, ('section',), rawtext[start:stop],
                       text[start:stop],
                       title=title, level=level, **kwargs)
        if len(t) > 4: # append subsections after subblocks
            for subsection in t[4]:
                self.children.append(Section(subsection, rawtext, text))

def parse_rust(rawtext, sections=None, **kwargs):
    'top level block parser, returns list of sections'
    if sections is None:
        sections = []
    text = [line.strip() for line in rawtext]
    for t in get_section_forest(rawtext, text):
        sections.append(Section(t, rawtext, text, **kwargs))
    return sections

def parse_file(filename, **kwargs):
    'read RUsT from specified file'
    with open(filename, 'rU') as ifile:
        rawtext = ifile.read().split('\n')
    return parse_rust(rawtext, **kwargs)
    
def parse_files(filenames, **kwargs):
    'read RUsT from specified files'
    sections = []
    for filename in filenames:
        with open(filename, 'rU') as ifile:
            rawtext = ifile.read().split('\n')
        parse_rust(rawtext, sections, **kwargs)
    return sections
    
def index_rust(forest, d=None):
    'build flat index of block IDs'
    if d is None:
        d = {}
    for tree in forest:
        for node in tree.walk():
            if len(node.tokens) > 1:
                d[node.tokens[1]] = node
    return d

def parse_select(rawtext):
    'parse a SELECT directive text, return forest of Block nodes'
    results = []
    stack = []
    for line in rawtext:
        tokens = line.strip().split()
        if not tokens or tokens[0] == '..': # comment, ignore
            continue
        if tokens[0] != '*':
            raise ValueError('not a list element: ' + line)
        node = Block([':select:', tokens[1]], None, None)
        params = {}
        for param in tokens[2:]: # copy parameter settings to node
            k,v = [s.strip() for s in param.split('=')]
            params[k] = v
        node.selectParams = params
        indent = line.index('*')
        while stack and stack[-1][0] >= indent: # pop stack if not within
            stack.pop()
        if stack: # add as child of existing node
            stack[-1][1].children.append(node)
        else: # save as top-level node
            results.append(node)
        stack.append((indent, node)) # push onto stack
    return results

def apply_select(forest, sourceDict, templateDict={} ,**kwargs):
    'add formatted text to :select: nodes drawing content from sourceDict'
    children = []
    for node in forest:
        nodeParams = kwargs.copy()
        nodeParams.update(getattr(node, 'selectParams', {}))
        subchildren = apply_select(node.children, sourceDict,
                                   templateDict, **nodeParams)
        if node.tokens[0] == ':select:':
            sourceNode = sourceDict[node.tokens[1]]
            sourceNode.add_metadata_attrs()
            if not subchildren:
                subchildren = sourceNode.children
            formatID = nodeParams.get('format', None)
            if formatID:
                t = templateDict[formatID]
                s = t.render(this=sourceNode, children=subchildren,
                             indented=indented, directive=directive,
                             **nodeParams)
                node.text = s.split('\n')
            else:
                node.text = sourceNode.text
            children.append(node)
    return children

def indented(indent, lines):
    'indent the lines based on the indent prefix'
    space = ' ' * len(indent)
    if not isinstance(lines, list):
        lines = lines.split('\n')
    lines = [indent + lines[0]] + [space + line for line in lines[1:]]
    return '\n'.join(lines)

def directive(name, v, text):
    'make a ReST directive'
    return indented('.. ', '%s:: %s\n\n%s' % (name, v, text))


def read_formats(filename):
    'get format dictionary from the RUsT file'
    rust = parse_file(filename)
    formatDict = {}
    for tree in rust:
        for node in tree.walk():
            if node.tokens[0] == ':format:':
                s = '\n'.join(node.text)
                t = Template(s)
                formatDict[node.tokens[1]] = t
    return formatDict

def test_select(sourceFiles=('bayes.rst', 'modeling.rst'),
                selectFile='hw1.rst',
                formatFile='formats.rst'):
    'basic test of applying select directive to source content'
    formatDict = read_formats(formatFile)
    source = parse_files(sourceFiles)
    sourceDict = index_rust(source)
    selection = parse_file(selectFile)
    apply_select(selection, sourceDict, formatDict,
                 insertVspace='', insertPagebreak=False)
    return selection

def get_text(forest):
    l = []
    for tree in forest:
        for node in tree.walk():
            try:
                l += node.text
            except AttributeError:
                pass
    return '\n'.join(l)

if __name__ == '__main__':
    import sys
    try:
        infile, outfile = sys.argv[1:]
    except ValueError:
        print 'usage: %s INRSTFILE OUTRSTFILE' % sys.argv[0]
    s = test_select(selectFile=infile)
    with open(outfile, 'w') as ofile:
        ofile.write(get_text(s))
