import graphviz

def make_slides_and_csv(ctfile, title='Concept Tests'):
    'produces CSV for PIP to load, and RST for rst2beamer to convert'
    ctstem = ctfile.split('.')[0]
    questions = graphviz.parse_rst(ctfile, {}, {}, {})
    print 'writing', ctstem + '.csv'
    graphviz.save_question_csv(questions, ctstem + '.csv') # for PIP
    slides = graphviz.add_answers(questions)
    rstout =  ctstem + '_slides.rst'
    print 'writing', rstout
    graphviz.write_rst_sections(rstout, slides, title)
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

if __name__ == '__main__':
    import sys
    rstout = make_slides_and_csv(*sys.argv[1:])
    make_tex(rstout)

