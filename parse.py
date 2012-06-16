
sectionChars = '!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
minTitle = 4

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
                yield lastStart, i, title, level
            title, step, mark = section
            i += step
            lastStart = i
            if mark not in levels:
                levels.append(mark)
            level = levels.index(mark)
        else:
            i += 1
    if not_empty(text[lastStart:]):
        yield lastStart, len(text), title, level
                

def is_block_start(i, rawtext, text, blockTokens):
    tokens = text[i].split()
    if tokens and tokens[0] in blockTokens:
        start = i + 1
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
        return start, i, tokens

def generate_blocks(rawtext, text,
                    blockTokens=(':question:', ':answer:', ':error:')):
    lastStart = i = 0
    n = len(rawtext)
    while i < n:
        block = is_block_start(i, rawtext, text, blockTokens)
        if block:
            yield block
            i = block[1]
        else:
            i += 1
            

def parse_block2(text, block, indent, subindent=None):
    while rawline in text:
        line = rawline.strip()
        if line:
            if subindent:
                if not rawline.startswith(subindent):
                    text.rewind()
                    return
            elif not rawline.startswith(indent):
                text.rewind()
                return
            else:
                subindent = rawline[:rawline.index(line[0])]

            c = rawline[0]
            if c in sectionChars and line == c * len(line) \
               and len(line) >= minTitle:
                pass
            lastline = line

def parse_rust(text):
    return conceptGraph, conceptDict, parseTree
