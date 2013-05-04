import pymongo
import jsonpickle
import json
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
        
            

def jsonize_docs(docs):
    'transform docs to JSON style dicts that mongodb can save'
    return [json.loads(jsonpickle.encode(doc)) for doc in docs]

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
        _id = d['_id']
        del d['_id']
        s = json.dumps(d)
        o = jsonpickle.decode(s)
        o._id = _id
        return o


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
    srcfiles = parse.find_source_files(srcpath)
    tree = parse.parse_files(srcfiles)
    docs = extract_docs(tree)
    insert_docs(docs, **kwargs)
    formats = extract_formats(tree)
    insert_formats(formats, **kwargs)

