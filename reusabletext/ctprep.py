import parse
import graphviz
import csv
import shutil
import subprocess
import warnings


def make_slides_and_csv(ctfile, imagepath, title='Concept Tests'):
    'produces CSV for Socraticqs to load, and RST for rst2beamer to convert'
    tree = parse.process_select(ctfile)
    questions = get_questions(tree)
    ctstem = ctfile.split('.')[0]
    print 'writing', ctstem + '.csv'
    save_question_csv(questions, ctstem + '.csv', parse.PostprocDict,
                      imagepath)
    rstout =  ctstem + '_slides.rst'
    print 'writing', rstout
    with open(rstout, 'w') as ofile:
        ofile.write(parse.get_text(tree))
    return rstout, tree

def make_tex(slidesfile, usePDFPages=False):
    'convert RST slides to TEX using rst2beamer'
    import rst2beamer
    description = 'rst2beamer output'
    filestem = slidesfile.split('.')[0]
    texfile = filestem + '.tex'
    argv = ['--overlaybullets=false', slidesfile, texfile]
    if usePDFPages:
        argv.insert(1, '--use-pdfpages')
    print 'writing', texfile
    rst2beamer.publish_cmdline(writer=rst2beamer.BeamerWriter(),
                               description=description,
                               argv=argv)
    return texfile

def get_questions(tree):
    'extract questions from select tree, as flat Document'
    result = parse.Document()
    for node in tree.walk():
        if getattr(node, 'tokens', ('skip',))[0] == ':question:' \
               and hasattr(node, 'selectParams'):
            result.append(node)
    return result

def get_html(lines, **kwargs):
    s = '\n'.join(lines)
    return graphviz.trivial_html(s, **kwargs)

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

def save_question_csv(questions, csvfile, postprocDict,
                      imagePath=None):
    ofile = open(csvfile, 'w')
    writer = csv.writer(ofile)
    imageFiles = []
    for t in generate_question_attrs(questions, postprocDict, imageFiles):
        errorModels = t[4]
        data = t[:4] + (len(errorModels),) + tuple(errorModels)
        if t[0] == 'mc':
            correct, choices = t[5:]
            data = data + (correct,) + tuple(choices)
        writer.writerow(data)
    if imageFiles:
        if imagePath:
            for path in imageFiles:
                try:
                    shutil.copy(path, imagePath)
                    print 'Copied', path
                except IOError:
                    warnings.warn('failed: copy %s %s' 
                                  % (path,imagePath))
        else:
            print 'WARNING: no path to copy image files:', imageFiles
    ofile.close()


def check_fileselect(tree):
    'check whether document contains fileselect nodes'
    for node in tree.walk():
        if getattr(node, 'tokens', ('ignore',))[0] == ':fileselect:':
            return True

if __name__ == '__main__':
    import sys
    try:
        infile, imagepath = sys.argv[1:]
    except ValueError:
        print 'usage: %s INRSTFILE IMAGEDIR' % sys.argv[0]
    rstout, tree = make_slides_and_csv(infile, imagepath)
    usePDFPages = check_fileselect(tree) # do we need pdfpages package?
    texfile = make_tex(rstout, usePDFPages) # generate beamer latex
    print 'running pdflatex...'
    subprocess.call(['pdflatex', texfile])
