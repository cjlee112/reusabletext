import os
import shutil
import urllib2
import subprocess
import warnings
import codecs
try:
    from jinja2 import Template
except ImportError:
    pass

sectionChars = '!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
minTitle = 4
defaultBlocks = (':question:', ':answer:', ':error:', ':intro:',
                 ':warning:', ':comment:', ':informal-definition:',
                 ':formal-definition:', ':derivation:',
                 '.. select::', ':format:', ':multichoice:',
                 )

# do not extract standard docutils directive options as RUsT metadata
docutilsMetadata = set((':width:',':alt:', ':height:', ':scale:',
                        ':align:', ':target:', ':figwidth:',
                        ':figclass:', ':subtitle:', ':header:',
                        ':widths:', ':header-rows:', ':stub-columns:',
                        ':file:', ':url:', ':encoding:',
                        ':delim:', ':quote:', ':keepspace:', ':escape:',
                        ':depth:', ':local:', ':backlinks:',
                        ':prefix:', ':suffix:', ':start:', ':ltrim:',
                        ':rtrim:', ':trim:', ':start-line:', ':end-line:',
                        ':start-after:', ':end-before:', ':literal:',
                        ':code:', ':number-lines:', ':tab-width:',
                        ':Author:', ':Authors:', ':Organization:', 
                        ':Contact:', ':Address:', ':Version:', ':Status:', 
                        ':Date:', ':Copyright:', ':Dedication:', ':Abstract:', 
                        ))

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
        tokens = ['.. select::', text[i][11:].lstrip()]
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

def split_items(rawtext, text, bullet='* '):
    'split a ReST item list into separate item texts'
    l = []
    skip = len(bullet)
    for i,line in enumerate(text):
        if line.startswith(bullet):
            pos = rawtext[i].index(bullet) + skip
            itemstart = rawtext[i][:pos]
            for j,line in enumerate(rawtext[i:]):
                if line.startswith(itemstart):                    
                    l.append(i + j)
            l.append(len(text))
            break
    if not l:
        return ()
    items = []
    for i,j in enumerate(l[:-1]):
        item = [text[j][skip:]] + text[j + 1:l[i + 1]]
        items.append(item)
    return items
    

def is_metadata(line, excludeTags=docutilsMetadata):
    'matches any line beginning with :foobar: pattern'
    if line and line[0] == ':':
        token = line.split()[0]
        tokens = token.split(':')
        return len(tokens) == 3 and len(token) > 2 and \
               tokens[2] == '' and token not in excludeTags
            

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

class BlockBase(object):
    def __init__(self):
        pass
    def copy(self):
        'deep copy of this object'
        c = BlockBase()
        c.__class__ = self.__class__
        c.tokens = tuple(self.tokens)
        if hasattr(self, 'title'):
            c.title = self.title
        if hasattr(self, 'filepath'):
            c.filepath = self.filepath
        if hasattr(self, 'text'):
            c.text = self.text
        if hasattr(self, 'children'):
            c.children = list(self.children)
        if hasattr(self, 'metadata'):
            c.metadata = list(self.metadata)
        if hasattr(self, '_metadata'):
            c._metadata = self._metadata.copy()
        return c
    def walk(self):
        'DFS traversal of the tree'
        for c in self.children:
            for node in c.walk():
                yield node
        yield self
    def walk_bfs(self):
        'BFS traversal of the tree'
        yield self
        for c in self.children:
            for node in c.walk_bfs():
                yield node
    def metadata_dict(self):
        '''save metadata as dict values containing list of one
        or more values'''
        try:
            return self._metadata
        except AttributeError:
            pass
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

    def child_dict(self, d=None, postprocDict={}):
        if d is None:
            d = {}
        for c in self.children:
            if c.tokens and getattr(c, 'text', False):
                attr = c.tokens[0][1:-1]
                v = c.text
                try:
                    f = postprocDict[attr]
                except KeyError:
                    pass
                else: # run postprocessor
                    v = f(self, v)
                try:
                    d[attr].append(v)
                except KeyError:
                    d[attr] = [v]
        return d

    def add_metadata_attrs(self, postprocDict={}):
        'add metadata as attributes on this obj'
        self.__dict__.update(self.metadata_dict())
        self.__dict__.update(self.child_dict(None, postprocDict))

    def __getstate__(self):
        d = dict(tokens=getattr(self, 'tokens', ()), 
                 metadata=self.metadata_dict(),
                 text=getattr(self, 'text', ()), 
                 title=getattr(self, 'title', ()),
                 children=self.children)
        try:
            d['tokenID'] = self.tokens[1]
        except (AttributeError, IndexError):
            pass
        return d
    def __setstate__(self, d):
        self.tokens = d['tokens']
        self._metadata = d['metadata']
        self.text = d['text']
        self.title = d['title']
        self.children = d['children']
        self.add_metadata_attrs(PostprocDict)


class Block(BlockBase):
    'a RUsT block, containing text and / or subblocks'
    def __init__(self, tokens, rawtext, text, indent=0,
                 blockTokens=defaultBlocks, filepath=None, mongoIndex=None,
                 mongoFormats=None, **kwargs):
        self.tokens = tokens
        self.indent = indent
        self.filepath = filepath
        self.__dict__.update(kwargs)
        if tokens[0] == '.. select::':
            result = parse_select(rawtext, text, tokens[1], filepath, 
                                  mongoIndex=mongoIndex,
                                  mongoFormats=mongoFormats)
            if result is None: # couldn't process, so just leave as text
                self.text = text
                self.children = []
            else:
                self.children = result
        elif rawtext: # parse sub-blocks, metadata
            self.parse(rawtext, text, blockTokens, mongoIndex=mongoIndex,
                       mongoFormats=mongoFormats)
        else: # empty
            self.text = text
            self.children = []
    def parse(self, rawtext, text, blockTokens, **kwargs):
        'parse into sub-blocks, if any, and extract metadata'
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
                                  text[start + 1:stop], indent, blockTokens,
                                  self.filepath, parent=self, **kwargs))
        if not_empty(text[stop:]):
            addtext, metadata = \
                     extract_metadata(rawtext[stop:], text[stop:], self.indent)
            self.text += addtext
            self.metadata += metadata
        self.children = children

    def get_children(self, token):
        for c in self.children:
            if c.tokens and c.tokens[0] == token:
                yield c
    def list_repr(self, textFunc, postprocDict):
        'get list of dict representation of this subtree'
        if self.tokens[0] == '.. select::': # replace by list of children
            l = []
            for c in self.children:
                l += c.list_repr(textFunc, postprocDict)
            return l
        elif self.tokens[0] == ':select:': # apply template formatting
            text = get_text_select(self, postprocDict)
            d = dict(text=textFunc(text), kind='selection')
            try:
                d['title'] = self.selectParams['title']
            except (KeyError, AttributeError):
                pass
        else: # just return dict of metadata and child attrs
            d = dict(text=textFunc(self.text), kind=self.tokens[0][1:-1])
            if len(self.tokens) >= 2 and self.tokens[1]:
                d['rustID'] = self.tokens[1]
            d.update(self.metadata_dict())
            if 'title' in d:
                d['title'] = ' '.join(d['title'])
            for k, v in self.child_dict(postprocDict=postprocDict).items():
                if k == 'multichoice':
                    for text in v[0]: # add as lettered item list
                        d['text'] = d['text'] + '\n\nA. ' + ' '.join(text)
                else:
                    d[k] = [textFunc(text) for text in v]
        return [d]
        

class Section(Block):
    'a ReST section, containing text, subblocks and / or subsections'
    def __init__(self, t, rawtext, text, blockTokens=defaultBlocks,
                 filepath=None, **kwargs):
        start, stop, title, level = t[:4]
        Block.__init__(self, ('section',), rawtext[start:stop],
                       text[start:stop], blockTokens=blockTokens,
                       filepath=filepath,
                       title=(title,), level=level, **kwargs)
        if len(t) > 4: # append subsections after subblocks
            for subsection in t[4]:
                self.children.append(Section(subsection, rawtext, text,
                                             blockTokens=blockTokens,
                                             filepath=filepath))
        for line in getattr(self, 'metadata', ()):
            if line.startswith(':ID:'): # extract section ID
                self.tokens = ('section', line.split()[1])
            if line.startswith(':defines:'): # extract concept ID
                self.conceptID = line.split()[1]
        for i,line in enumerate(text[start:stop]):
            if line.startswith('.. glossary::'):
                save_glossary(self, i, rawtext[start:stop], text[start:stop])
    def list_repr(self, textFunc, postprocDict):
        'get list of dicts repr of this subtree'
        l = []
        d = dict(text=textFunc(self.text), kind='section',
                 title=' '.join(self.title),
                 level=self.level)
        if len(self.tokens) >= 2 and self.tokens[1]:
            d['rustID'] = self.tokens[1]
        d.update(self.metadata_dict())
        children = []
        for c in self.children:
            if isinstance(c, Section): # treat subsections as children
                children += c.list_repr(textFunc, postprocDict)
            else: # do not treat blocks as children
                l += c.list_repr(textFunc, postprocDict)
        if children:
            d['children'] = children
        if d['title'] or children: # include this section if not empty
            l = [d] + l
        return l

def save_glossary(node, start, rawtext, text):
    'save glossary as node list on node.glossary'
    subindent = subindent2 = None
    indent = get_indent(start, rawtext, text)
    i = start + 1
    while i < len(text): # find 1st indented glossary term
        subindent = get_indent(i, rawtext, text)
        if subindent is not None:
            break
        i += 1
    if not subindent or subindent <= indent:
        raise ValueError('empty glossary directive!')
    k = None
    l = []
    v = []
    subindent3 = 0
    while i < len(text): # read glossary definitions
        subindent2 = get_indent(i, rawtext, text)
        if subindent2 is not None:
            if subindent2 < subindent:
                break
            elif subindent2 == subindent:
                if k: # save previous definition
                    l.append((k, v))
                k = text[i] # start a new definition
                v = []
                i += 1
                subindent3 = 0
                continue
            elif subindent3 == 0: # save first def line indentation
                subindent3 = subindent2
        v.append(rawtext[i][subindent3:])
        i += 1
    if k: # save the last glossary definition
        l.append((k, v))
    if l: # save glossary as node list
        nodes = []
        for k,v in l:
            nodes.append(Block(('glossary', k), None, v, 0, (), node.filepath))
        node.glossary = nodes

                
class Document(BlockBase):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.children = []
    def append(self, v):
        self.children.append(v)
    def list_repr(self, textFunc, postprocDict):
        'list of dicts repr of the tree'
        l = []
        for c in self.children:
            l += c.list_repr(textFunc, postprocDict)
        return l

def parse_rust(rawtext, filepath=None, doc=None, **kwargs):
    'top level block parser, returns list of sections'
    if doc is None:
        doc = Document()
    text = [line.strip() for line in rawtext]
    for t in get_section_forest(rawtext, text):
        doc.append(Section(t, rawtext, text, filepath=filepath, **kwargs))
    return doc

def parse_rust_docinfo(rawtext, filepath=None, doc=None, **kwargs):
    doc = parse_rust(rawtext, filepath, doc, **kwargs)
    title = author = None
    if len(doc.children) > 0:
        for s in doc.children[0].text:
            if s.startswith('.. title::'):
                title = s[11:]
            elif s.startswith(':Author:'):
                author = s[8:].strip()
    return doc, title, author

def parse_file(filename, **kwargs):
    'read RUsT from specified file'
    with codecs.open(filename, 'rU', encoding='utf-8') as ifile:
        rawtext = ifile.read().split('\n')
    return parse_rust(rawtext, filename, **kwargs)
    
def parse_files(filenames, **kwargs):
    'read RUsT from specified files'
    doc = Document()
    for filename in filenames:
        with open(filename, 'rU') as ifile:
            rawtext = ifile.read().split('\n')
        parse_rust(rawtext, filename, doc, **kwargs)
    return doc


class MultiDict(dict):
    'instead of over-writing existing key, add numbered variant k.2, k.3 etc.'
    def __setitem__(self, k, v):
        i = 2
        k0 = k
        while self.get(k, v) != v:
            k = '%s.%d' % (k0, i)
            i += 1
        dict.__setitem__(self, k, v)

def standardize_identifier(s, replacements={',':';', '(':'', ')':''}):
    'remove / replace characters not allowed in identifiers'
    s = '_'.join(s.split()) # replace whitespace
    for k,v in replacements.items():
        s = s.replace(k, v)
    return s
    

def index_rust(tree, d=None, formatDict=None):
    'build flat index of block IDs'
    if d is None:
        d = MultiDict()
    if formatDict is None:
        formatDict = {}
    for node in tree.walk():
        for line in getattr(node, 'metadata', ()):
            if line.startswith(':proves:'): # extract concept.proof
                k = standardize_identifier(line.split()[1]) + '.proof'
                d[k] = node
        try:
            k = standardize_identifier(node.conceptID) + '.definition'
            d[k] = node
        except AttributeError:
            pass
        try:
            conceptID = standardize_identifier(node.parent.conceptID)
        except AttributeError:
            conceptID = None
        if hasattr(node, 'glossary'):
            for gnode in node.glossary:
                term = standardize_identifier(gnode.tokens[1])
                k = 'glossary.' + term
                d[k] = gnode
        if hasattr(node, 'tokens'):
            if len(node.tokens) > 1:
                if node.tokens[0] == ':format:':
                    s = '\n'.join(node.text)
                    formatDict[node.tokens[1]] = Template(s)
                else:
                    d[standardize_identifier(node.tokens[1])] = node
            elif conceptID: # save in conceptID.token format
                k = conceptID + '.' + node.tokens[0].split(':')[1]
                d[k] = node
    return d, formatDict

def find_source_files(srcpath, filterFunc=lambda s:s.endswith('.rst')):
    srcfiles = []
    for dirpath, dirnames, filenames in os.walk(srcpath):
        if os.path.exists(os.path.join(dirpath, '.rust_ignore')):
            continue # do not index files in this directory
        for filename in filenames:
            if filterFunc(filename):
                srcfiles.append(os.path.join(dirpath, filename))
    return srcfiles

def load_source_path(srcpath, ongoing=[], **kwargs):
    srcpath = os.path.abspath(srcpath)
    if srcpath in ongoing:
        print 'WARNING: infinite .. select:: loop blocked:', srcpath
        return None
    ongoing.append(srcpath) # push onto stack so we can detect infinite loop
    ## try:
    ##     return selectIndexCache[srcpath]
    ## except KeyError:
    ##     pass
    if os.path.isdir(srcpath): # walk directory for all files
        srcfiles = find_source_files(srcpath, **kwargs)
    else: # single file
        srcfiles = [srcpath]
    tree = parse_files(srcfiles)
    ongoing.pop() # all done, so pop from stack
    d = index_rust(tree)
    ## selectIndexCache[srcpath] = d
    return d

def parse_select_item(item):
    'extract item and associated params from text list'
    line = item[0]
    tokens = line.strip().split()
    params = {}
    for param in tokens[1:]: # copy parameter settings to node
        k,v = [s.strip() for s in param.split('=')]
        params[k] = v
    for pline in item[1:]: # copy metadata as parameters to node
        if pline:
            k = pline.split()[0]
            if k[0] == ':' and k[-1] == ':':
                params[k[1:-1]] = pline[len(k):].strip()
            else:
                raise ValueError('bad SELECT parameter line: ' + pline)
    return tokens[0], params

def parse_select(rawtext, text, srcpath, filepath, mongoIndex=None,
                 mongoFormats=None):
    'parse a SELECT directive text, return forest of :select: nodes'
    if srcpath.startswith('http:') or srcpath.startswith('https:'):
        srcpath = download_file(srcpath) # download local file
    else:
        srcpath = expand_path(srcpath, filepath)
    if os.path.isfile(srcpath) and not srcpath.lower().endswith('.rst'):
        return parse_file_select(rawtext, text, srcpath, filepath)
    if srcpath.startswith('mongodb:'):
        if not mongoIndex or not mongoFormats:
            raise ValueError('attempted to select from mongodb but no mongoIndex')
        srcDict, formatDict = mongoIndex, mongoFormats
    else:
        t = load_source_path(srcpath)
        if t is None: # blocked infinite loop, so can't process directive
            return None
        srcDict, formatDict = t
    results = []
    stack = []
    for item in split_items(rawtext, text):
        sourceID, params = parse_select_item(item)
        node = Block((':select:',), None, None, sourceID=sourceID,
                     filepath=filepath)
        node.selectParams = params
        node.srcDict = srcDict
        node.formatDict = formatDict
        results.append(node)
        ## indent = line.index('*')
        ## while stack and stack[-1][0] >= indent: # pop stack if not within
        ##     stack.pop()
        ## if stack: # add as child of existing node
        ##     stack[-1][1].children.append(node)
        ## else: # save as top-level node
        ##     results.append(node)
        ## stack.append((indent, node)) # push onto stack
    return results

try:
    includePDFformats = {
        'includepdf':Template('''
.. raw:: latex

   %%rst2beamer:endframe

   \includepdf[ {{- selectArgs -}} ]{ {{- srcpath -}} }

   %%

''')
    }
except NameError:
    includePDFformats = {}

def expand_path(path, relativeToFile):
    'expand env vars, ~, relative to file path if not absolute'
    path = os.path.expanduser(os.path.expandvars(path))
    relativeToDir = os.path.dirname(relativeToFile)
    return os.path.join(relativeToDir, path)

def mkdir_if_needed(dirpath):
    'create the directory if needed'
    try:
        os.makedirs(dirpath)
    except OSError:
        if not os.path.isdir(dirpath):
            raise


def convert_to_pdf(srcpath, pdfDir='_converted_pdf',
                   cmd=['unoconv', '-f', 'pdf']):
    'convert external format to PDF for pdf page selection'
    stem = os.path.basename(srcpath)
    pos = stem.rfind('.')
    if pos >= 0:
        stem = stem[:pos] # remove .suffix from filename
    pdfpath = os.path.join(pdfDir, stem + '.pdf')
    if os.path.isfile(pdfpath) and \
       os.path.getmtime(pdfpath) > os.path.getmtime(srcpath):
        warnings.warn('%s already converted, cached as %s'
                      % (srcpath, pdfpath))
        return pdfpath # up to date, no need to do anything
    mkdir_if_needed(pdfDir)
    cmd += ['-o', pdfDir, srcpath]
    warnings.warn('Converting %s to PDF; this might take a minute or so...'
                  % srcpath)
    print ' '.join(cmd) # print the command so user can see it...
    try:
        subprocess.check_call(cmd) # run the conversion
    except OSError:
        try:
            os.unlink(pdfpath) # ensure that we don't leave a bad copy
        except:
            pass
        raise OSError('PDF conversion failed: unable to run %s' % cmd[0])
    return pdfpath
    
def parse_pdf_select(rawtext, text, srcpath, filepath,
                     formatDict=includePDFformats):
    'extract PDF pages using includepdf latex'
    results = []
    for item in split_items(rawtext, text):
        selectArgs, params = parse_select_item(item)
        selectParams = dict(format='includepdf', selectArgs=selectArgs,
                            srcpath=srcpath)
        node = Block((':fileselect:',), None, None, selectParams=selectParams,
                     filepath=filepath, formatDict=formatDict)
        results.append(node)
    return results

def download_file(url, downloadDir='_downloaded'):
    'get the specified URL and return the downloaded file path'
    path = os.path.join(downloadDir, url.split('/')[-1])
    path = os.path.abspath(path)
    if os.path.isfile(path): # already downloaded, nothing to do
        warnings.warn('%s already downloaded, cached as %s' % (url, path))
        return path
    mkdir_if_needed(downloadDir)
    warnings.warn('Downloading %s...' % url)
    req = urllib2.urlopen(url)
    try:
        with open(path, 'wb') as ifile:
            shutil.copyfileobj(req, ifile) # save the file contents
    except BaseException as e: # catch all possible errors
        try:
            os.unlink(path) # ensure that we don't leave a bad copy
        except:
            pass
        raise e # report the original error
    return path
    

def parse_file_select(rawtext, text, srcpath, filepath):
    'toplevel fileselect dispatcher'
    if not srcpath.lower().endswith('.pdf'):
        srcpath = convert_to_pdf(srcpath) # try to convert to PDF
    return parse_pdf_select(rawtext, text, srcpath, filepath)

def parse_select_list(s, srcDict):
    'extract [ID1,ID2...] list starting at this point, or return None'
    if s[0] == '[': # start of a list
        sources = []
        for sourceID in s[1:].split(']')[0].split(','):
            sources.append(srcDict[sourceID])
        return sources, s.index(']') + 1

def parse_select_dict(s, srcDict):
    'extract {key=EXPR,key2=EXPR...} starting at this point, or return None'
    if s[0] == '(': # start of a dict
        d = {}
        start = 0
        tokens = s[1:].split(')')[0].split('=')
        for i,k in enumerate(tokens[:-1]):
            k = k[start:]
            t = parse_select_list(tokens[i + 1], srcDict)
            if t: # save select-list record
                d[k] = t[0]
                if t[1] < len(tokens[i + 1]) and tokens[i + 1][t[1]] != ',':
                    raise ValueError('missing comma in select-dict')
                start = t[1] + 1 # skip past the comma
            else: # treat as single ID
                sourceID = tokens[i + 1].split(',')[0]
                d[k] = srcDict[sourceID]
                start = len(sourceID) + 1 # skip past the comma
        return d, s.index(')') + 1
                
        
def apply_select(tree):
    'replace :select: nodes with desired content from node.srcDict'
    for i,node in enumerate(tree.children):
        if node.tokens[0] == ':select:':
            t = parse_select_dict(node.sourceID, node.srcDict)
            if t: # save a dict of source nodes
                node.selectParams.update(t[0])
            else:
                t = parse_select_list(node.sourceID, node.srcDict)
                if t: # save a list of source nodes
                    node.selectParams['sources'] = t[0]
                else: # single ID node
                    sourceNode = node.srcDict[node.sourceID]
                    c = sourceNode.copy()
                    c.selectParams = node.selectParams
                    c.formatDict = node.formatDict
                    tree.children[i] = c # source node replaces target node
        else: # recurse down tree
            apply_select(node)

def indented(indent, lines):
    'indent the lines based on the indent prefix'
    space = ' ' * len(indent)
    if not isinstance(lines, list):
        lines = lines.split('\n')
    lines = [indent + lines[0]] + [space + line for line in lines[1:]]
    return '\n'.join(lines)

def directive(name, v, text):
    'make a ReST directive'
    if isinstance(text, list):
        return indented('.. ', ['%s:: %s' % (name, v)] + text)
    else:
        return indented('.. ', '%s:: %s\n\n%s' % (name, v, text))


def read_formats(filename):
    'get format dictionary from the RUsT file'
    tree = parse_file(filename)
    formatDict = {}
    for node in tree.walk():
        if getattr(node, 'tokens', ('ignore',))[0] == ':format:':
            s = '\n'.join(node.text)
            t = Template(s)
            formatDict[node.tokens[1]] = t
    return formatDict

def itemsplit_pp(node, rawtext):
    'treat as ReST item list, split into list of items'
    text = [line.strip() for line in rawtext]
    return split_items(rawtext, text)

def multichoice_pp(node, rawtext):
    'remove :correct: tag, set node.correct, and return list of items'
    items = itemsplit_pp(node, rawtext)
    for i,c in enumerate(items):
        try:
            pos = c[-1].index(':correct:') # assume tag on last line
        except ValueError:
            pass
        else:
            node.correct = i
            c[-1] = c[-1][:pos]
            break
    return items

def process_select(selectFile):
    'read RUsT containing SELECT statements, process them'
    selection = parse_file(selectFile)
    apply_select(selection)
    return selection


def get_text_select(node, postprocDict, **kwargs):
    'get template formatted text from :select: node'
    node.add_metadata_attrs(postprocDict)
    for c in node.children:
        c.add_metadata_attrs(postprocDict)
    nodeParams = kwargs.copy()
    nodeParams.update(node.selectParams)
    try:
        formatID = nodeParams['format']
    except KeyError:
        return getattr(node, 'text', [])
    t = node.formatDict[formatID]
    s = t.render(this=node, children=node.children,
                 indented=indented, directive=directive,
                 getattr=getattr, len=len, int=int,
                 kwargs=nodeParams, **nodeParams)
    return [s]

def get_text_list(tree, postprocDict, **kwargs):
    'walk tree and extract text, applying bound templates'
    l = []
    for node in tree.children:
        if hasattr(node, 'selectParams'):
            l += get_text_select(node, postprocDict, **kwargs)
        else:
            title = getattr(node, 'title', (None,))[0]
            if title: # add reST title
                l += [title, '-' * len(title)]
            l += getattr(node, 'text', [])
            l += get_text_list(node, postprocDict, **kwargs)
    return l

# define metadata that require post-processing
PostprocDict = {'multichoice':multichoice_pp}

def get_text(tree, postprocDict=PostprocDict, **kwargs):
    l = get_text_list(tree, postprocDict, **kwargs)
    return u'\n'.join(l)

if __name__ == '__main__':
    import sys
    try:
        infile, outfile = sys.argv[1:]
    except ValueError:
        print 'usage: %s INRSTFILE OUTRSTFILE' % sys.argv[0]
    tree = process_select(infile)
    with open(outfile, 'w') as ofile:
        ofile.write(get_text(tree))
