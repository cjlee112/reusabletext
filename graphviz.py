import glob

class Section(object):
    ''
    def __init__(self, title):
        self.title = title
        self.text = title + '\n' + '-' * len(title) + '\n'
        self.lastline = ''
        self.metadata = []

    def add_metadata(self, *args):
        self.metadata.append(args)

    def add_text(self, text):
        self.text += self.lastline
        self.lastline = text

    def drop_lastline(self):
        self.lastline = ''

    def __str__(self):
        return self.text + self.lastline

def parse_rst(filename, g, parent, colors,
              colorDict=dict(motivates='yellow', illustrates='orange',
                             tests='green')):
    ifile = open(filename)
    l = []
    section = None
    for rawline in ifile:
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
        elif line.startswith(':motivates:'):
            target = line.split()[1]
            g.setdefault(node, {})[target] = dict(label='motivates',
                                                  color='yellow') # add edge
        elif line.startswith(':depends:'):
            sources = line.split()[1].split(',')
            for source in sources:
                try:
                    g[source][node] = dict(label='depends')
                except KeyError:                    
                    g.setdefault(source, {})[node] = dict(label='depends')
                    colors[source] = 'gray'
        elif line.startswith(':tests:'):
            colors[node] = 'green'
            targets = line.split()[1].split(',')
            for target in targets:
                g.setdefault(node, {})[target] = dict(label='tests',
                                                      color='green')
        elif line.startswith(':violates:'):
            colors[node] = 'red'
            targets = line.split()[1].split(',')
            for target in targets:
                g.setdefault(node, {})[target] = dict(label='violates',
                                                      color='red')
        elif line.startswith(':contains:'):
            targets = line.split()[1].split(',')
            for target in targets:
                parent[target] = node
        elif l: # in a section, so append to its text, preserving whitespace
            section.add_text(rawline)
        lastLine = line
    ifile.close()
    return l

def filter_files(rulefile, outfile):
    'compile output from rst sources by filtering with rulefile'
    ifile = open(rulefile, 'rU')
    ofile = open(outfile, 'w')
    sections = None
    try:
        for rawline in ifile:
            line = rawline.strip()
            if line[0] == rawline[0]: # file path to filter
                if sections:
                    apply_filters(ofile, sections, filters)
                sections = parse_rst(line, {}, {}, {})
                filters = []
            else:
                filters.append(line)
        if sections:
            apply_filters(ofile, sections, filters)
    finally:
        ofile.close()
        ifile.close()

def apply_filters(ofile, sections, filters):
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
                    ofile.write(str(s))
        else: # just a regular title filter
            notFound = True
            for s in sections:
                if s.title.startswith(f):
                    ofile.write(str(s))
                    notFound = False
            if notFound:
                raise ValueError('no match for title: ' + f)
        
                    
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
