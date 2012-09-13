import parse
import graphviz
import csv
import shutil
import subprocess


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
    return rstout

def make_tex(slidesfile):
    'convert RST slides to TEX using rst2beamer'
    import rst2beamer
    description = 'rst2beamer output'
    filestem = slidesfile.split('.')[0]
    texfile = filestem + '.tex'
    argv = ['--overlaybullets=false', slidesfile, texfile]
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

def save_question_csv(questions, csvfile, postprocDict,
                      imagePath=None):
    ofile = open(csvfile, 'w')
    writer = csv.writer(ofile)
    imageFiles = []
    for q in questions.children:
        q.add_metadata_attrs(postprocDict)
        s = get_html(q.text, filepath=q.filepath, imageList=imageFiles)
        answer = get_html(q.answer[0], filepath=q.filepath,
                          imageList=imageFiles)
        errorModels = [get_html(e) for e in getattr(q, 'error', ())]
        if hasattr(q, 'multichoice'): # multiple choice format
            choices = [get_html(c) for c in q.multichoice[0]]
            writer.writerow(('mc', q.title[0], s, answer, len(errorModels))
                            + tuple(errorModels) + (q.correct,) + tuple(choices))
        else:
            writer.writerow(('text', q.title[0], s, answer, len(errorModels))
                            + tuple(errorModels))
    if imageFiles:
        if imagePath:
            for path in imageFiles:
                print 'Copying', path
                shutil.copy(path, imagePath)
        else:
            print 'WARNING: no path to copy image files:', imageFiles
    ofile.close()
            

if __name__ == '__main__':
    import sys
    try:
        infile, imagepath = sys.argv[1:]
    except ValueError:
        print 'usage: %s INRSTFILE IMAGEDIR' % sys.argv[0]
    rstout = make_slides_and_csv(infile, imagepath)
    texfile = make_tex(rstout) # generate beamer latex
    print 'running pdflatex...'
    subprocess.call(['pdflatex', texfile])
