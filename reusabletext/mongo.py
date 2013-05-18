import pymongo
import jsonpickle
import json
import os.path
try:
    from jinja2 import Template
except ImportError:
    pass

def extract_docs(doc, level=1):
    'get list of top-level sections and questions, each as parse tree'
    l = []
    if getattr(doc, 'level', 0) < level:
        for c in doc.children:
            l += extract_docs(c, level)
        return l
    children = []
    for c in doc.children:
        if getattr(c, 'tokens', ('mismatch',))[0] == ':question:':
            l.append(c)
        else:
            children.append(c)
    doc.children = children
    l.append(doc)
    return l

def extract_formats(tree):
    'get dict of named template strings'
    d = {}
    for node in tree.walk():
        tokens = getattr(node, 'tokens', ())
        if len(tokens) >= 2 and tokens[0] == ':format:':
            d[tokens[1]] = '\n'.join(node.text)
    return d
        
def combine_text(doc):
    'combine text lists from a doc tree'
    l = list(getattr(doc, 'text', ()))
    for c in doc.children:
        l += combine_text(c)
    return l
    
            

def jsonize_docs(docs):
    'transform docs to JSON style dicts that mongodb can save'
    l = []
    for doc in docs:
        d = json.loads(jsonpickle.encode(doc)) # create a dictionary
        d['content'] = '\n'.join(combine_text(doc)) # searchable text string
        try: # get title attr or metadata
            d['title'] = '\n'.join(doc.title)
        except AttributeError:
            m = []
            for s in getattr(doc, 'metadata', ()):
                if s.startswith(':title: '):
                    m.append(s[8:])
            if m:
                d['title'] = '\n'.join(m)
        l.append(d)
    return l

def init_collection(dbName='socraticqs', collName='latest', **kwargs):
    client = pymongo.MongoClient(**kwargs)
    db = client[dbName]
    db.drop_collection(collName)
    coll = db[collName]
    coll.create_index([('title', 'text'), ('content', 'text')],
                      weights=dict(title=10, content=1))
    return coll

def get_collection(dbName='socraticqs', collName='latest', **kwargs):
    client = pymongo.MongoClient(**kwargs)
    db = client[dbName]
    coll = db[collName]
    return coll


def insert_docs(docs, coll=None, **kwargs):
    'save docs to db using jsonpickle'
    if coll is None:
        coll = get_collection(**kwargs)
    coll.insert(jsonize_docs(docs))

def insert_formats(formatDict, coll=None, collName='formats', **kwargs):
    'save formats to db'
    if coll is None:
        coll = get_collection(collName=collName, **kwargs)
    l = [dict(_id=t[0], template=t[1]) for t in formatDict.items()]
    coll.insert(l)

def text_search(coll, query, limit=50):
    d = coll.database.command('text', coll.name, search=query,
                              projection=dict(content=False), limit=limit)
    l = []
    for docDict in d['results']:
        o = unpickle_json(docDict['obj'])
        l.append((o, docDict['score']))
    return l

def unpickle_json(d):
    _id = d['_id']
    del d['_id']
    s = json.dumps({'py/object':d['py/object'], 'py/state':d['py/state']})
    o = jsonpickle.decode(s)
    o._id = _id
    return o


class DocIDIndex(object):
    'dict interface to doc collection in mongodb'
    def __init__(self, coll=None, **kwargs):
        if coll is None:
            coll = get_collection(**kwargs)
        self.coll = coll
    def __getitem__(self, k):
        d = self.coll.find_one({'py/state.tokenID':k})
        if d is None:
            raise KeyError('ID %s not found' % k)
        return unpickle_json(d)

class FormatIndex(object):
    'dict interface to formats stored in mongodb'
    def __init__(self, coll=None, collName='formats', **kwargs):
        if coll is None:
            coll = get_collection(collName=collName, **kwargs)
        self.coll = coll
        self.d = {}
    def __getitem__(self, k):
        try:
            return self.d[k]
        except KeyError:
            pass
        d = self.coll.find_one({'_id':k})
        if d is None:
            raise KeyError('ID %s not found' % k)
        t = Template(d['template'])
        self.d[k] = t
        return t


def get_indexes(srcpath):
    'get doc and format index interfaces to the db'
    return DocIDIndex(), FormatIndex()

def save_rust_repo(srcpath, **kwargs):
    'save rust and formats to database'
    import parse
    path = os.path.join(srcpath, 'sourcefiles.txt')
    with open(path, 'rU') as ifile:
        srcfiles = [os.path.join(srcpath, s.strip()) for s in ifile]
    tree = parse.parse_files(srcfiles)
    docs = extract_docs(tree)
    insert_docs(docs, **kwargs)
    print 'inserted %d documents' % len(docs)
    path = os.path.join(srcpath, 'formats.rst')
    tree = parse.parse_files([path])
    formats = extract_formats(tree)
    insert_formats(formats, **kwargs)
    print 'inserted %d formats' % len(formats)

