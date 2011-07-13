import glob

def parse_rst(filename, g, parent, colors):
    ifile = open(filename)
    for line in ifile:
        line = line.strip()
        if len(line) > 1 and line == '-' * len(line): # section start
            node = title = lastLine
        elif line.startswith(':defines:'):
            node = line.split()[1]
            g.setdefault(node, {}) # add node to graph
            colors[node] = 'black'
        elif line.startswith(':link:'):
            source, relation, target = line.split()[1:]
            g.setdefault(source, {})[target] = dict(label=title)
        elif line.startswith(':proves:'):
            target = line.split()[1]
            g.setdefault(node, {})[target] = dict(label='proves') # add edge
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
        lastLine = line
    ifile.close()
    
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
