import graphviz

def make_qa_rst(rstfile, qtitle='Questions', atitle='Answers'):
    rststem = rstfile.split('.')[0]
    sections = graphviz.parse_rst(rstfile, {}, {}, {})
    questions = graphviz.filter_questions(sections)
    qa = graphviz.add_answers(questions)
    answers = [qa[i] for i in range(1, len(qa), 2)]
    rstout = rststem + '_q.rst'
    print 'writing', rstout
    graphviz.write_rst_sections(rstout, questions, qtitle)
    rstout = rststem + '_a.rst'
    print 'writing', rstout
    graphviz.write_rst_sections(rstout, answers, atitle)

if __name__ == '__main__':
    import sys
    make_qa_rst(*sys.argv[1:])

    
