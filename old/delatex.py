import re

def replace_delimiters(latex, start, end, repl, replCR=None, stripFirstCR=True):
    i = 0
    t = ''
    offset = len(start)
    skip = len(end)
    while True:
        j = latex[i:].find(start)
        if j < 0:
            break
        j += i
        k = latex[j:].index(end)
        field = latex[j + offset: j + k]
        if stripFirstCR and field[0] == '\n':
            field = field[1:]
        if replCR is not None:
            field = re.sub(r'\n', replCR, field)
        t += latex[i:j] + repl % field
        i = j + k + skip
    t += latex[i:] # save tail of document
    return t

def convert_equations(latex):
    t = re.sub(r'\$([^$]+)\$', r':math:`\1`', latex)
    t = replace_delimiters(t, r'\[', r'\]', '\n.. math:: %s', '\n          ')
    t = replace_delimiters(t, r'\begin{equation}\n', r'\end{equation}',
                           '.. math:: %s', '\n          ')
    return t

def convert_emph(latex):
    t = replace_delimiters(latex, r'{\em ', '}', '*%s*')
    return t

def normalize_cr(latex):
    t = re.sub(r'\r\n', r'\n', latex)
    t = re.sub(r'\r', r'\n', t)
    return t


def convert_quotes(latex):
    t = re.sub('``', '"', latex)
    t = re.sub("''", '"', t)
    return t
    


def convert_sections(latex, headings=('chapter', 'section', 'subsection',
                                      'subsubsection'), markers='#-.+'):
    i = 0
    starts = ['\\' + heading + '{' for heading in headings]
    t = ''
    skip = 1
    while True:
        l = []
        for k,start in enumerate(starts): 
            j = latex[i:].find(start)
            if j >= 0:
                l.append((j, k))
        if len(l) == 0:
            break
        l.sort() # find closest marker
        j = i + l[0][0]
        k = l[0][1]
        end = latex[j:].index('}')
        title = latex[j + len(starts[k]):j + end]
        t += latex[i:j] + '\n' + title + '\n' + markers[k] * len(title) + '\n'
        i = j + end + skip
    t += latex[i:] # save tail of document
    return t


def convert_lists(latex, headings=('itemize', 'enumerate'),
                  markers=('*', '#.')):
    i = level = 0
    t = ''
    starts = [r'\begin{' + heading + '}' for heading in headings]
    ends = [r'\end{' + heading + '}' for heading in headings]
    listType = []
    indent = [0]
    while True:
        l = []
        for k,start in enumerate(starts): # search for begin / end markers
            j = latex[i:].find(start)
            if j >= 0:
                l.append((j + i, k, 'start'))
            j = latex[i:].find(ends[k])
            if j >= 0:
                l.append((j + i, k, 'end'))
        if level > 0: # search for item markers
            j = latex[i:].find(r'\item')
            if j >= 0:
                l.append((j + i, listType[-1], 'item'))
        if len(l) == 0: # no more markers
            break
        l.sort() # find closest marker
        j, k, action = l[0]
        if action == 'item': # indent an item
            s = re.sub(r'\n', r'\n' + ' ' * indent[-1], latex[i:j])
            t += s + '\n' + ' ' * indent[-2] + markers[k]
            i = j + 5
            if latex[i] == '\n':
                i += 1
                if latex[i] != ' ':
                    t += ' '
        elif action == 'start': # push a level
            level += 1
            indent.append(indent[-1] + len(markers[k]) + 1)
            listType.append(k)
            t += latex[i:j]
            i = j + len(starts[k])
        else: # pop a level
            t += re.sub(r'\n', r'\n' + ' ' * indent[-1], latex[i:j])
            level -= 1
            indent.pop()
            listType.pop()
            i = j + len(ends[k])
    t += latex[i:] # save tail of document
    return t
            
def convert_latex(latex):
    'apply all conversions to reST'
    t = normalize_cr(latex)
    t = convert_equations(t)
    t = convert_emph(t)
    t = convert_sections(t)
    t = convert_lists(t)
    t = convert_quotes(t)
    return t

if __name__ == '__main__':
    import sys
    ifile = open(sys.argv[1])
    print convert_latex(ifile.read())
    ifile.close()
