import re
import glob
import csv

class Section(object):
    ''
    def __init__(self, title):
        self.title = title
        self.text = ''
        self.lastline = ''
        self.metadata = []

    def add_metadata(self, label, data):
        self.metadata.append((label, data))

    def get_metadata(self, label, *args):
        for tag, data in self.metadata:
            if tag == label:
                return data
        if len(args) > 0: # caller provided a default value, so return it
            return args[0]
        raise KeyError('metadata not found: ' + label)

    def add_text(self, text):
        self.text += self.lastline
        self.lastline = text

    def get_text(self):
        return self.text + self.lastline

    def drop_lastline(self):
        self.lastline = ''

    def __str__(self):
        'return restructured text with title'
        return self.title + '\n' + '-' * len(self.title) + '\n' \
               + self.text + self.lastline

def add_metadata(section, label, *args):
    if section:
        section.add_metadata(label, *args)

def parse_rst(filename, g, parent, colors,
              colorDict=dict(motivates='yellow', illustrates='orange',
                             tests='green')):
    ifile = open(filename)
    l = []
    section = None
    it = iter(ifile)
    for rawline in it:
        line = rawline.strip()
        if len(line) > 1 and line == '-' * len(line): # section start
            if section: # last line is NOT part of previous section
                section.drop_lastline()
            node = title = lastLine
            section = Section(title)
            l.append(section)
        elif line.startswith(':defines:'):
            node = line.split()[1]
            g.setdefault(node, {}) # add node to graph
            colors[node] = 'black'
            add_metadata(section, 'defines', node)
        elif line.startswith(':link:'):
            source, relation, target = line.split()[1:]
            relation = relation[1:-1]
            if node not in g:
                g.setdefault(node, {}) # add node to graph
                parent[node] = source
                if source not in g:
                    g.setdefault(source, {}) # add node to graph
                    colors[source] = 'gray'
                source = node
                label = relation
                try:
                    colors[node] = colorDict[relation]
                except KeyError:
                    pass
            else:
                label = title
            edgeDict = dict(label=label)
            try:
                edgeDict['color'] = colorDict[relation]
            except KeyError:
                pass
            g.setdefault(source, {})[target] = edgeDict
        elif line.startswith(':proves:'):
            target = line.split()[1]
            g.setdefault(node, {})[target] = dict(label='proves') # add edge
            add_metadata(section, 'proves', target)
        elif line.startswith(':motivates:'):
            target = line.split()[1]
            g.setdefault(node, {})[target] = dict(label='motivates',
                                                  color='yellow') # add edge
            add_metadata(section, 'motivates', target)
        elif line.startswith(':depends:'):
            sources = line.split()[1].split(',')
            for source in sources:
                try:
                    g[source][node] = dict(label='depends')
                except KeyError:                    
                    g.setdefault(source, {})[node] = dict(label='depends')
                    colors[source] = 'gray'
            add_metadata(section, 'depends', sources)
        elif line.startswith(':tests:'):
            colors[node] = 'green'
            targets = line.split()[1].split(',')
            for target in targets:
                g.setdefault(node, {})[target] = dict(label='tests',
                                                      color='green')
            add_metadata(section, 'tests', targets)
        elif line.startswith(':violates:'):
            colors[node] = 'red'
            targets = line.split()[1].split(',')
            for target in targets:
                g.setdefault(node, {})[target] = dict(label='violates',
                                                      color='red')
            add_metadata(section, 'violates', targets)
        elif line.startswith(':contains:'):
            targets = line.split()[1].split(',')
            for target in targets:
                parent[target] = node
            add_metadata(section, 'contains', targets)
        elif line.startswith(':answer:'):
            add_metadata(section, 'answer', line[9:])
        elif line.startswith(':start-answer:'):
            answer = line[15:]
            for rawline in it:
                line = rawline.strip()
                if line.startswith(':end-answer:'):
                    break
                else:
                    answer += line
            add_metadata(section, 'answer', answer)
        elif l: # in a section, so append to its text, preserving whitespace
            section.add_text(rawline)
        lastLine = line
    ifile.close()
    return l

def filter_files(rulefile):
    'generate selected sections from rst sources by filtering with rulefile'
    ifile = open(rulefile, 'rU')
    sections = None
    try:
        for rawline in ifile:
            line = rawline.strip()
            if line[0] == rawline[0]: # file path to filter
                if sections:
                    for s in apply_filters(sections, filters):
                        yield s
                sections = parse_rst(line, {}, {}, {})
                filters = []
            else:
                filters.append(line)
        if sections:
            for s in apply_filters(sections, filters):
                yield s
    finally:
        ifile.close()

def apply_filters(sections, filters):
    'output selected sections using simple filter rules'
    it = iter(filters)
    for f in it:
        if f.startswith('('): # begins an inclusion block
            start = f[1:]
            skip = []
            for f in it:
                if f.startswith('-'): # a section title to skip
                    skip.append(f[1:])
                elif f.startswith(')'): # ends an inclusion block
                    stop = f[1:]
                    break
                else:
                    raise ValueError('unexpected label in (block): ' + f)
            for i,s in enumerate(sections):
                if s.title.startswith(start):
                    break
            if i >= len(sections):
                raise ValueError('(block) start not found: ' + start)
            for s in sections[i:]:
                if s.title.startswith(stop):
                    break
                show = True
                for t in skip:
                    if s.title.startswith(t):
                        show = False
                        break
                if show:
                    yield s
        else: # just a regular title filter
            notFound = True
            for s in sections:
                if s.title.startswith(f):
                    yield s
                    notFound = False
            if notFound:
                raise ValueError('no match for title: ' + f)

def write_rst_sections(path, sections):
    'output sections in reST format'
    ofile = open(path, 'w')
    for s in sections:
        ofile.write(str(s))
    ofile.close()


def line_iter(s):
    i = 0
    j = s.find('\n')
    while j >= 0:
        yield s[i:j + 1]
        i = j + 1
        j = s.find('\n', i)
    if i < len(s):
        yield s[i:]

def parse_directive(line):
    dlabel = line.split(':')[0]
    try:
        content = line[line.index('::') + 2:] + '\n'
    except ValueError: # just a comment, not a directive
        return None
    return content, (dlabel,)

def question_html(content, directive):
    if directive == 'figure':
        return '<IMG SRC="%s">\n' % content.split('\n')[0]
    elif directive == 'math':
        return '$$%s$$\n' % content

def list_html(content):
    return '<LI>' + content + '</LI>\n'

def replace_block(s, start, parsefunc, subfunc, **kwargs):
    it = line_iter(s)
    try:
        rawline = it.next()
    except StopIteration:
        return ''
    t = ''
    while True:
        line = rawline.strip()
        if line.startswith(start):
            offset = rawline.find(line[0])
            rawline = None
            result = parsefunc(line[len(start):])
            if result:
                content, args = result
                for rawline in it: # read the entire block
                    if rawline[offset].isspace(): # inside block
                        content += rawline
                        rawline = None
                    else: # end of block
                        break
                t += subfunc(content, *args, **kwargs) # perform substitution
        else: # just append regular text
            t += rawline
            rawline = None
        if not rawline: # need to read another line
            try:
                rawline = it.next()
            except StopIteration:
                break
    return t

def echo_line(line):
    return line, ()

def append_choice(content, choices):
    choices.append(' '.join(content.split('\n')))
    return ''

def trivial_html(s):
    s = re.sub(r':math:`([^`]*)`', r'\(\1\)', s)
    s = replace_block(s, '.. ', parse_directive, question_html)
    s = replace_block(s, '* ', echo_line, list_html)
    return s

def replace_newlines(s):
    s = s.strip()
    l = s.split('\n') # replace newlines with space and <BR>
    result = []
    empty = False
    for s in l:
        if s == '':
            empty = True
        else:
            if empty: # paragraph separator
                result.append('<BR><BR>')
                empty = False
            result.append(s)
    return ' '.join(result)

def save_question_csv(questions, csvfile, imagetag='Draw a'):
    ofile = open(csvfile, 'w')
    writer = csv.writer(ofile)
    for q in questions:
        s = q.get_text()
        s = trivial_html(s)
        choices = []
        s = replace_block(s, '#. ', echo_line, append_choice, choices=choices)
        s = replace_newlines(s)
        answer = q.get_metadata('answer', '')
        answer = trivial_html(answer)
        answer = replace_newlines(answer)
        if choices:
            writer.writerow(('mc', q.title, s, answer) + tuple(choices))
        elif s.find(imagetag) >= 0:
            writer.writerow(('image', q.title, s, answer))
        else:
            writer.writerow(('text', q.title, s, answer))
    ofile.close()
                    
def parse_files(path='*.rst'):
    g = {}
    parent = {}
    colors = {}
    for filename in glob.glob(path):
        parse_rst(filename, g, parent, colors)
    return g, parent, colors

class Graphviz(object):
    'simple dot format writer; handles nested subgraphs correctly, unlike gvgen'
    def __init__(self):
        self.content = {}
        self.edges = {}
        self.nodes = []
        self.toplevel = []
        self.nodeID = {}

    def _save_node(self, label):
        try:
            return self.nodeID[label]
        except KeyError:
            i = len(self.nodes)
            self.nodes.append(dict(label=label))
            self.nodeID[label] = i
            return i

    def add_node(self, label, parent=None, color=None):
        nodeID = self._save_node(label)
        if color:
            self.nodes[nodeID]['color'] = color
        if parent is not None:
            parentID = self._save_node(parent)
            self.content.setdefault(parentID, []).append(nodeID)
        elif nodeID not in self.toplevel:
            self.toplevel.append(nodeID)

    def add_edge(self, node1, node2, edgeDict=None):
        self.edges.setdefault(self.nodeID[node1], {})[self.nodeID[node2]] \
                                                  = edgeDict

    def dot_attrlist(self, d, sep=', '):
        return sep.join([('%s="%s"' % t) for t in d.items()])

    def print_branch(self, ifile, node, level=1):
        prespace = '  ' * level
        try:
            children = self.content[node]
        except KeyError:
            print >>ifile, prespace + self.node_repr(node) + ' [' + \
                  self.dot_attrlist(self.nodes[node]) + '];'
        else:
            nodeAttrs = self.nodes[node].copy()
            nodeAttrs['color'] = 'white'
            print >>ifile, prespace + self.node_repr(node) \
                  + ' {\n  ' + prespace + 'node' + str(node) + ' [' \
                  + self.dot_attrlist(nodeAttrs) + '];'
            for child in children:
                self.print_branch(ifile, child, level + 1)
            print >>ifile, prespace + '};'

    def node_repr(self, node):
        if node in self.content:
            return 'subgraph cluster' + str(node)
        else:
            return 'node' + str(node)

    def edge_attrlist(self, d):
        if d:
            return ' [' + self.dot_attrlist(d) + ']'
        else:
            return ''

    def print_dot(self, ifile):
        print >>ifile, 'digraph G {\ncompound=true;'
        prespace = '  '
        for node in self.toplevel:
            self.print_branch(ifile, node)
        for node, edges in self.edges.items():
            for node2,edge in edges.items():
                print >>ifile, prespace + self.node_repr(node) \
                      + '->' + self.node_repr(node2) \
                      + self.edge_attrlist(edge) + ';'
        print >>ifile, '}'


def save_graphviz(filename, g, parent={}, colors={}, containsEdge=True):
    nodes = set(g.keys())
    for targets in g.values():
        for node in targets:
            nodes.add(node)
    gv = Graphviz()
    d = {}
    for node in nodes:
        if containsEdge:
            gv.add_node(node, color=colors.get(node, None))
        else:
            gv.add_node(node, parent.get(node, None), colors.get(node, None))
    for node, targets in g.items():
        for target, edge in targets.items():
            gv.add_edge(node, target, edge)
    if containsEdge:
        for node, container in parent.items():
            gv.add_edge(container, node, dict(color='blue', label='contains'))
    ifile = open(filename, 'w')
    gv.print_dot(ifile)
    ifile.close()
