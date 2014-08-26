import parse
import graphviz
import csv
import shutil
import subprocess
import warnings
import os.path
import codecs
import re
try:
    import pypandoc
except ImportError:
    pass

def make_slides_and_csv(ctfile, imagepath, title='Concept Tests', 
                        globalErrors=()):
    'produces CSV for Socraticqs to load, and RST for rst2beamer to convert'
    tree = parse.process_select(ctfile)
    questions = get_questions(tree)
    ctstem = ctfile.split('.')[0]
    print 'writing', ctstem + '.csv'
    save_question_csv(questions, ctstem + '.csv', parse.PostprocDict,
                      imagepath, globalErrors=globalErrors)
    rstout =  ctstem + '_slides.rst'
    print 'writing', rstout
    with codecs.open(rstout, 'w', encoding='utf-8') as ofile:
        ofile.write(parse.get_text(tree))
    return rstout, tree

def make_tex(slidesfile, usePDFPages=False, beamerTheme=None, docTitle=None):
    'convert RST slides to TEX using rst2beamer'
    import rst2beamer
    description = 'rst2beamer output'
    filestem = slidesfile.split('.')[0]
    texfile = filestem + '.tex'
    argv = ['--overlaybullets=false', '--output-encoding=utf-8', 
            slidesfile, texfile]
    if usePDFPages:
        argv.insert(1, '--use-pdfpages')
    if beamerTheme:
        argv.insert(1, '--theme=' + beamerTheme)
    if docTitle:
        argv.insert(1, '--doctitle=' + docTitle)
    print 'writing', texfile
    rst2beamer.publish_cmdline(writer=rst2beamer.BeamerWriter(),
                               description=description,
                               argv=argv)
    # fix docutils output so pdflatex will work
    with codecs.open(texfile, 'rb', encoding='utf-8') as ifile:
        s = ifile.read().replace(r'\usepackage[utf8]{inputenc}',
                                 r'\usepackage[utf8x]{inputenc}')
    with codecs.open(texfile, 'wb', encoding='utf-8') as ifile:
        ifile.write(s)
    return texfile

def get_questions(tree):
    'extract questions from select tree, as flat Document'
    result = parse.Document()
    for node in tree.walk():
        if getattr(node, 'tokens', ('skip',))[0] == ':question:' \
               and hasattr(node, 'selectParams') \
               and 'answer' in node.child_dict():
            result.append(node)
    return result

def get_html(lines, **kwargs):
    s = '\n'.join(lines)
    return graphviz.trivial_html(s, **kwargs)

def rst2md(lines, startMath=r'\(', endMath=r'\)'):
    r'''convert, preserving inline math as \(inlinemath\)
    and display math as \[math\]'''
    txt = '\n'.join(lines)
    #txt = re.sub(':math:`([^`]+)`', r'INLINEMATHSTART`\1`INLINEMATHEND', txt)
    s = ''
    lastpos = 0
    l = []
    while True: # replace all :math: with unique markers
        i = txt.find(':math:`', lastpos)
        if i < 0:
            break
        s += txt[lastpos:i]
        lastpos = i + 7
        i = txt.find('`', lastpos)
        if i < 0: # missing terminator, so treat as regular text
            break
        marker = 'mArKeR:%d:' % len(l)
        l.append((marker, txt[lastpos:i]))
        s += marker
        lastpos = i + 1 # skip past ` terminator
    s += txt[lastpos:]
    txt = pypandoc.convert(s, 'md', format='rst')
    s = ''
    lastpos = 0
    for marker, math in l: # put them back in after conversion
        i = txt.find(marker, lastpos)
        if i < 0:
            continue # must have been removed by comment, so ignore
        s += txt[lastpos:i] + startMath + math + endMath # reinsert math
        lastpos = i + len(marker)
    s += txt[lastpos:]
    txt = re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', s, flags=re.DOTALL) # use \[math\]
    return txt
    
def flag_rst_images(lines, tag='STATICIMAGE/'):
    'prefix all local image files with specified tag'
    s = '\n'.join(lines)
    return re.sub(r'\.\. image::\s+([^/\s]+)', r'.. image:: %s\1' % tag, s)
        


def generate_question_attrs(questions, postprocDict, imageFiles):
    for q in questions.children:
        q.add_metadata_attrs(postprocDict)
        s = get_html(q.text, filepath=getattr(q, 'filepath', None), 
                     imageList=imageFiles)
        answer = get_html(q.answer[0], 
                          filepath=getattr(q, 'filepath', None),
                          imageList=imageFiles)
        errorModels = [get_html(e) for e in getattr(q, 'error', ())]
        if hasattr(q, 'multichoice'): # multiple choice format
            choices = [get_html(c) for c in q.multichoice[0]]
            yield ('mc', q.title[0], s, answer, errorModels,
                   q.correct, choices)
        else:
            yield ('text', q.title[0], s, answer, errorModels)

def question_tuple(q, globalErrors=(), func=flag_rst_images):
    q.add_metadata_attrs(parse.PostprocDict)
    conceptID = getattr(q, 'tests', ('',))[0]
    if conceptID == 'something': # filter out stupid place-holders
        conceptID = ''
    elif conceptID:
        conceptID = ' '.join(conceptID.split('_'))
    t = (len(q.tokens) >= 2 and q.tokens[1] or '',
         conceptID,
         getattr(q, 'title', ('',))[0],
         func(q.text),
         func(getattr(q, 'answer', ('',))[0])) + \
        tuple([func(e) for e in getattr(q, 'error', ())]) + globalErrors
    return t

def generate_question_tuple(ctfile, globalErrors=(), func=flag_rst_images):
    '''yields (ID, concepts, title, question, answer, error1, error2...)
    tuples with text conversion by func'''
    tree = parse.process_select(ctfile)
    questions = get_questions(tree)
    for q in questions.children:
        yield question_tuple(q, globalErrors, func)

def save_ctfiles_csv(ctfiles, csvdir='.', **kwargs):
    'process multiple ctfiles (using .. select::) to csv courselets output'
    for ctfile in ctfiles:
        ctbase = os.path.basename(ctfile)
        csvfile = os.path.join(csvdir, ctbase.split('.')[0] + '.csv')
        print 'Writing', csvfile
        with codecs.open(csvfile, 'w', encoding='utf-8') as ofile:
            writer = csv.writer(ofile)
            for row in generate_question_tuple(ctfile, **kwargs):
                writer.writerow(row)
    
def save_question_csv(questions, csvfile, postprocDict,
                      imagePath=None, imageSource=None, globalErrors=()):
    ofile = open(csvfile, 'w')
    writer = csv.writer(ofile)
    imageFiles = []
    for t in generate_question_attrs(questions, postprocDict, imageFiles):
        errorModels = tuple(t[4]) + globalErrors
        data = t[:4] + (len(errorModels),) + errorModels
        if t[0] == 'mc':
            correct, choices = t[5:]
            data = data + (correct,) + tuple(choices)
        writer.writerow(data)
    if imageFiles:
        if imagePath:
            for path in imageFiles:
                if imageSource:
                    path = os.path.join(imageSource, path)
                try:
                    shutil.copy(path, imagePath)
                    print 'Copied', path
                except IOError:
                    warnings.warn('failed: copy %s %s' 
                                  % (path,imagePath))
        else:
            print 'WARNING: no path to copy image files:', imageFiles
    ofile.close()


def get_concept_links(metadata, links=('defines', 'motivates', 'depends',
                                       'tests', 'violates', 'proves')):
    l = []
    for relation in links:
        for concepts in metadata.get(relation, ()):
            for conceptID in concepts.split(','):
                l.append((relation, conceptID))
    return l

def save_section_csv(lesson, metadata, writer, func, token='lesson',
                     linkParent=None):
    rustID = metadata.get('ID', ('',))[0]
    sourceDB, sourceID = metadata.get('sourceDB', (':',))[0].split(':')
    data = (token, lesson.nodeID, rustID,
            getattr(lesson, 'title', (' '.join(token.split('-')),))[0],
            func(lesson.text),
            sourceDB, sourceID)
    if linkParent:
        data += (linkParent,)
    writer.writerow(data)

def save_question_csv2(q, writer, func):
    t = question_tuple(q, func=func)
    data = ('question', q.nodeID, t[0]) + t[2:]
    writer.writerow(data)
    if q.parent and q.parent.tokens and q.parent.tokens[0] == ':question:':
        data = ('qlink', q.nodeID, 'qintro', q.parent.nodeID)
        writer.writerow(data)

def is_multipart_question(q):
    for c in q.children:
        if c.tokens[0] == ':question:':
            return True
    return False

def save_generic_error(error, writer):
    if '(ABORT)' in error:
        errorType = 'abort'
    else:
        errorType = 'fail'
    data = ('generic-error', error, errorType)
    writer.writerow(data)

def save_concept_error(lesson, metadata, writer, func):
    conceptID = metadata['violates'][0].split(',')[0]
    rustID = metadata['defines'][0].split(',')[0]
    lesson.conceptID = rustID # make children point to this ID
    data = ('error', lesson.nodeID, rustID, func(lesson.text), conceptID)
    writer.writerow(data)

def save_concept_lessons_csv(ctfiles, csvfile, func=flag_rst_images,
                             blocks=(':warning:', ':comment:', ':derivation:',
                                     ':intro:', ':informal-definition:',
                                     ':formal-definition:')):
    tree = parse.parse_files(ctfiles)
    with codecs.open(csvfile, 'w', encoding='utf-8') as ofile:
        writer = csv.writer(ofile)
        for error in defaultErrorModels:
            save_generic_error(error, writer)
        for i, lesson in enumerate(tree.walk()): # assign node IDs
            lesson.nodeID = i
        for lesson in tree.walk():
            if not hasattr(lesson, 'tokens'):
                continue
            metadata = lesson.metadata_dict()
            if 'fallacy' in metadata.get('conceptType', ()) \
              or 'violates' in metadata:
                save_concept_error(lesson, metadata, writer, func)
                continue # do not generate concept links
            elif lesson.tokens[0] == 'section':
                save_section_csv(lesson, metadata, writer, func)
            elif lesson.tokens[0] in blocks:
                if len(lesson.tokens) >= 2:
                    save_section_csv(lesson, metadata, writer, func,
                                    lesson.tokens[0][1:-1], lesson.tokens[1])
                elif lesson.parent and getattr(lesson.parent, 'conceptID', 0):
                    save_section_csv(lesson, metadata, writer, func,
                                     lesson.tokens[0][1:-1],
                                     lesson.parent.conceptID)
            elif lesson.tokens[0] == ':question:':
                if is_multipart_question(lesson):
                    save_section_csv(lesson, metadata, writer, func)
                else:
                    save_question_csv2(lesson, writer, func)
            for relation, conceptID in get_concept_links(metadata):
                if relation == 'defines':
                    lesson.conceptID = conceptID
                writer.writerow(('conceptlink', lesson.nodeID, relation,
                                 conceptID))

def check_fileselect(tree):
    'check whether document contains fileselect nodes'
    for node in tree.walk():
        if getattr(node, 'tokens', ('ignore',))[0] == ':fileselect:':
            return True

defaultErrorModels = (
    "some people misread the question (ABORT).",
    "some people didn't know a basic definition needed for this question (ABORT).",
    "some people couldn't figure out how to get started -- failed to apply concept(s) that they knew, e.g. due to 'trying to remember the answer' (ABORT).",
    "some people got hung up on a detail and didn't think through the main question (ABORT).",
    "This question is mis-phrased: its literal meaning doesn't really ask what you claimed (FAIL).",
)

if __name__ == '__main__':
    import sys
    try:
        infile, imagepath = sys.argv[1:]
    except ValueError:
        print 'usage: %s INRSTFILE IMAGEDIR' % sys.argv[0]
    rstout, tree = make_slides_and_csv(infile, imagepath, 
                                       globalErrors=defaultErrorModels)
    usePDFPages = check_fileselect(tree) # do we need pdfpages package?
    texfile = make_tex(rstout, usePDFPages) # generate beamer latex
    print 'running pdflatex...'
    subprocess.call(['pdflatex', texfile])
