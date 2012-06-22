
sectionChars = '!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
minTitle = 4
defaultBlocks = (':question:', ':answer:', ':error:', ':intro:')

def get_indent(i, rawtext, text):
    if text[i]:
        return rawtext[i].index(text[i][0])

def is_section_mark(i, rawtext, text):
    rawline = rawtext[i]
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
           and rawtext[i][0] == text[i][0]:
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
    level = None
    while i < n:
        section = is_section_start(i, rawtext, text)
        if section:
            if i > lastStart and not_empty(text[lastStart:i]):
                yield [lastStart, i, title, level]
            title, step, mark = section
            i += step
            lastStart = i
            if mark not in levels:
                levels.append(mark)
            level = levels.index(mark)
        else:
            i += 1
    if not_empty(text[lastStart:]):
        yield [lastStart, len(text), title, level]

def get_section_forest(rawtext, text):
    'convert generate_sections() list into trees'
    stack = [[]]
    for t in generate_sections(rawtext, text):
        level = t[3]
        if level > len(stack):
            raise ValueError('section level too big!  Debug!')
        elif level == len(stack):
            stack.append([t])
        else:
            for i in range(level + 1, len(stack)):
                subsections = stack.pop()
                stack[-1][-1].append(subsections)
            stack[-1].append(t)
    return stack[0] # top-level sections

def is_block_start(i, rawtext, text, blockTokens):
    tokens = text[i].split()
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
    def __init__(self, tokens, rawtext, text, indent=0, **kwargs):
        self.tokens = tokens
        self.indent = indent
        self.__dict__.update(kwargs)
        children = []
        for start, stop, tokens, indent in generate_blocks(rawtext, text):
            if not children and not_empty(text[:start]):
                self.text, self.metadata = \
                           extract_metadata(rawtext[:start], text[:start],
                                            self.indent)
            children.append(Block(tokens, rawtext[start + 1:stop],
                                  text[start + 1:stop], indent))
        if not children and not_empty(text):
            self.text, self.metadata = \
                           extract_metadata(rawtext, text, self.indent)
        self.children = children

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

def parse_rust(rawtext):
    'top level block parser, returns list of sections'
    sections = []
    text = [line.strip() for line in rawtext]
    for t in get_section_forest(rawtext, text):
        sections.append(Section(t, rawtext, text))
    return sections
    
