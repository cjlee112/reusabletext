############
ReusableText
############

What is ReusableText for?
-------------------------

The easiest way to understand it is to see it in action.
Say we have a set of files containing text for a textbook, including
some concise definitions, problems and solutions.  Say we'd like to
reuse some of this text to make slides for presenting in class.
We can do this easily, because in ReusableText the individual
"pieces" of text are tagged to say what they are (e.g. a question,
an answer, etc.), and to give them unique labels that allow us
to select from them at will.  Here are two small fragments illustrating
the ReusableText format (which is just a minor extension of the standard
`reStructuredText <http://docutils.sourceforge.net/rst.html>`_
format)::

  :question: snp_detection_prob
    :title: A SNP Detection Problem
    :tests: Projection_(statistics)
    You are using a microarray to detect single nucleotide polymorphisms
    (SNPs) in samples from multiple people.  For a given site you wish to 
    compare two hypotheses: :math:`H_1`, a SNP is present in the population
    (i.e. there is genetic variation at this site); :math:`H_0`, no SNP
    is present.  The microarray gives a fluorescence observation :math:`X`
    for a given sample, and you are given likelihoods
    :math:`p(X|\kappa)` for the possible number of copies of the variant
    in that sample :math:`\kappa=0,1,...2N`, where :math:`N` is the number
    of people pooled in that sample.  You are also given the two
    models :math:`p(\kappa|H_1,N), p(\kappa|H_0,N)`, and the prior ratio
    :math:`p(H_1)/p(H_0)`.  
  
    Given :math:`X` measurements for multiple samples as your *obs*, 
    can you compute the posterior odds ratio :math:`p(H_1|obs)/p(H_0|obs)`?
    :multichoice:
      * Yes, the data are sufficient. :correct:
      * No, the :math:`\kappa` values are unknown.
      * It depends.
    :answer:
      Yes, just sum over all possible values of :math:`\kappa`.

  ... lots more text ...

  Remember the Summation Principle!
  ---------------------------------
  :ID: snp_detection_prob_sumprin

  Even if we do not know the value of a hidden variable that
  appears in a probability expression, we can eliminate it
  from the expression by summing over all possible values
  of that variable.

  * If we don't want to know its value (a "nuisance variable"),
    we simply calculate the sum without recording the values of
    any of the individual terms.

  * Alternatively, by recording the value of each individual
    term in the joint probability sum, we can use Bayes' Law
    to compute the posterior probability distribution of 
    the hidden variable.

  * Actually this is exactly what Bayes' Law "pure inference"
    is doing: the individual terms are the *numerator* of
    Bayes' Law, and the total sum is the *denominator*.

  ... lots more text ...

(Of course, these pieces would be just part of a very large
set of text constituting the draft textbook).  

We can now output a new document by running the ReusableText
preprocessor on a text file that includes the following
``select`` directive (a key feature of ReusableText)::

  .. select:: ~/Documents/tb
     * snp_detection_prob format=multichoice_slide
     * snp_detection_prob_sumprin format=slide

The argument after the ``select::`` directive gives the
path to a file or directory containing the ReusableText database.

The ``multichoice_slide`` format is tailored to output a slide
posing a multiple choice question to the class, plus an additional
slide presenting the answer.  The ``slide`` format just follows
a standard beamer-style slide format.  It outputs the following
reStructuredText, which in turn will generates slides via
`rst2beamer <http://www.agapow.net/software/rst2beamer>`_ 
and ``pdflatex``::

  A SNP Detection Problem
  -----------------------

  You are using a microarray to detect single nucleotide polymorphisms
  (SNPs) in samples from multiple people.  For a given site you wish to 
  compare two hypotheses: :math:`H_1`, a SNP is present in the population
  (i.e. there is genetic variation at this site); :math:`H_0`, no SNP
  is present.  The microarray gives a fluorescence observation :math:`X`
  for a given sample, and you are given likelihoods
  :math:`p(X|\kappa)` for the possible number of copies of the variant
  in that sample :math:`\kappa=0,1,...2N`, where :math:`N` is the number
  of people pooled in that sample.  You are also given the two
  models :math:`p(\kappa|H_1,N), p(\kappa|H_0,N)`, and the prior ratio
  :math:`p(H_1)/p(H_0)`.  

  Given :math:`X` measurements for multiple samples as your *obs*, 
  can you compute the posterior odds ratio :math:`p(H_1|obs)/p(H_0|obs)`?


  #. Yes, the data are sufficient. 
  #. No, the :math:`\kappa` values are unknown.
  #. It depends.

  A SNP Detection Problem Answer
  ------------------------------

  Yes, just sum over all possible values of :math:`\kappa`.


  Remember the Summation Principle!
  ---------------------------------


  Even if we do not know the value of a hidden variable that
  appears in a probability expression, we can eliminate it
  from the expression by summing over all possible values
  of that variable.

  * If we don't want to know its value (a "nuisance variable"),
    we simply calculate the sum without recording the values of
    any of the individual terms.

  * Alternatively, by recording the value of each individual
    term in the joint probability sum, we can use Bayes' Law
    to compute the posterior probability distribution of 
    the hidden variable.

  * Actually this is exactly what Bayes' Law "pure inference"
    is doing: the individual terms are the *numerator* of
    Bayes' Law, and the total sum is the *denominator*.

But wait, there's more: we would also like the tool to generate
a "question file" for our in-class question system (Socraticqs,
a web servlet that students log in to during class to answer 
the questions we pose them).  Since the ReusableText processor
outputs a parse-tree from the ``select`` output, it provides
other tools that do this for us: with just
a few lines of Python code, ``ctprep.py`` pulls just the questions from
that tree, and writes the necessary CSV format for Socraticqs.
Now the students will automatically see the same questions
when they log in during class!

What is ReusableText?
---------------------

ReusableText is a minor but very useful extension of 
`reStructuredText <http://docutils.sourceforge.net/rst.html>`_ (reST),
the easy-to-use plain-text markup format.  It extends reST's
well-defined (but almost never used) metadata to provide
powerful ways of re-using your text, as a "database" of content
that you can select from and compile desired outputs at will.
It does this in two basic ways:

* **metadata tags and blocks**: while reST defines a format for
  inserting metadata in a document, it defines no way of using those
  metadata. ReusableText lets you define some metadata as *blocks*
  of text (a multiline block defined by indentation, as usual in reST),
  and treats the rest as *tags* (a single line key-value pair).
  These metadata are bound to their enclosing object (either a reST
  section or a ReusableText block).  Note that ReusableText blocks can
  be nested.  Blocks and sections are typically given unique identifiers
  for *selecting* them.
* **selection and template-based re-formatting**: ReusableText introduces
  a new directive **select** which allows you to insert any selection
  of blocks and selections (via their unique IDs) at any point in a
  ReusableText document.  Moreover, you can create any output you want
  out of those selected blocks, using customizable templates.

The ReusableText Format
-----------------------

metadata blocks and values
..........................

`reStructuredText <http://docutils.sourceforge.net/rst.html>`_
specifies that a token bracketed by colons (e.g. ``:header:``)
shall be treated as *metadata*.  However, the only place reST
uses metadata is for specifying option values in directives, e.g.::

  .. image:: my.png
     :width: 50%

ReusableText adds the concept of a **metadata block**, which
consists of a metadata tag followed by an optional identifier,
and then an indented block of text (which can itself contain
nested metadata blocks, regular metadata values, or any 
standard reST directives etc.).  For example::

  :question: hamlet_soliloquy
    :author: William Shakespeare
    :source: Hamlet, Act III
    To be, or not to be, that is the question:
    Whether 'tis Nobler in the mind to suffer...
    ... lots more text here ...

    .. image:: hamlet.png

    :comment:
      According to Wikipedia, this is one of the most famous
      literary quotations...
    :warning:
      There is deep disagreement on its meaning.        

Any amount of indentation can be used to define a block, but
it must be consistent (i.e. subsequent lines must match the
indentation of the first line; any non-empty line with less
indentation will terminate the block).  Two spaces are suggested
as the standard amount of indentation to use.

Currently, the set of allowed metadata blocks is set as a list
of metadata tags that are treated as metadata block starts.

All other metadata tags will be treated as **metadata values**,
i.e. a one-line tag:value pair.  The following metadata values
are treated specially:

* ``:ID:`` in a reST section, will tag that section with the
  associated value as the section's identifier (for the purposes
  of the ``select`` directive, see below).
* ``:title:`` in a ReusableText block, will be bound to that block
  as its title string.

The :format: metadata block
...........................

The ``:format:`` metadata block defines a Jinja2 template for 
reformatting text in a ``select`` directive.  It must have
an identifier.  Its indented text block is read as a Jinja2
template, allowing the following local variables:

* ``this``: the ReusableText object selected by the ``select``
  statement.  This will always be a reST section or ReusableText block.
  It has useful attributes, e.g. ``this.text`` is the list of its reST
  text lines (of the reST section or ReusableText block).  Note that
  ReusableText metadata values are bound to the object as attributes,
  e.g. ``this.title`` will access the title(s) for this section or
  block, etc.
* ``children``: the list of child nodes of ``this``, in the ReusableText
  parse tree.  E.g. if ``this`` is a multipart question, then
  ``children`` will be the list of sub-questions.

It also allows the following function calls:

* ``indented(indent, lines)``: ``indent`` must be a string
  representing an initial reST indentation line.  ``lines``
  must be a list of strings representing reST text.  The
  first line will be indented with ``indent``; all subsequent
  lines will be indented with spaces equal to the length of ``indent``.
  For example, to create a numbered list item::

    indented('#. ', lines)

* ``directive(name, v, text)``: creates a reST directive.  
  ``name`` must be the name of the desired reST directive (e.g. ``image``);
  ``v`` must be its associated value (e.g. ``foo.png``);
  ``text`` must be a list of text lines to be indented within the
  directive, if any.

Jinja2 Templating
.................

ReusableText just uses `Jinja2 <http://jinja.pocoo.org/>`_ 
to define whatever ``:format:`` templates you want.
Here's an example of the format::

  :format: question
    #. **{{- this.title[0] -}}**

    {{ indented('   ', this.text) }}

  :format: multipart-question
    #. **{{- this.title[0] -}}**
    {% if this.text %}
    {{ indented('   ', this.text) -}}
    {% endif %}
    {% for subq in children %}
    {{ indented('   #. ', subq.text) -}}

  :format: multipart-answer
    #. **{{- this.title[0] -}}**
    {% for subq in children %}
    {{ indented('   #. ', subq.answer[0]) -}}
    {% endfor %}

  :format: slide
    {{ this.title[0] + '\n' + '-' * len(this.title[0])}}

    {{ '\n'.join(this.text) }}

  :format: multichoice_slide
    {{ this.title[0] + '\n' + '-' * len(this.title[0])}}

    {{ '\n'.join(this.text) }}

    {% for clines in this.multichoice[0] %}
    {{ indented('#. ', clines) -}}
    {% endfor %}

    {{ this.title[0] + ' Answer\n' + '-' * (len(this.title[0]) + 7)}}

    {{ '\n'.join(this.answer[0]) }}

The select Directive
....................

ReusableText introduces a new directive, ``select``, which has
the following simple form::

  .. select:: path/to/database
     * sourceID1 format=some_format
     * sourceID2 format=another_format
     (etc.)

The *path to database* argument can be either a file, or a 
directory.  In the latter case, all files within that directory
(or subdirectories) with ``.rst`` suffix will be scanned.
The path can be absolute, relative, or user-relative (i.e.
any path beginning with ``~`` or ``~some_username`` will be
properly expanded to that user's home directory).

The content of the ``select`` directive must be a simple bullet list,
each consisting of one line, whose first token must be the identifier
of a section or block in the ReusableText source database, and 
whose subsequent tokens will be interpreted as key=value pairs.
The ``format`` value must be the identifier of a ``:format:``
defined in the ReusableText source database, to be used as
the Jinja2 template for formatting this content.

The ReusableText Pre-processor
------------------------------

Currently, ReusableText is implemented as a preprocessor that
takes ReUsableText inputs (i.e. a source database, and a 
document containing ``select`` directives to process), and
outputs standard reStructuredText, which can then be
compiled via Sphinx, docutils, rst2beamer, etc. to any number
of different output forms (slides, reports etc.).

The standard preprocessor command is ``parse.py``::

  python /path/to/reusabletext/parse.py infile outfile

runs the preprocessor on the ``select`` document specified by
``infile``, and writes reST output to ``outfile``.

A second command ``ctprep.py`` generates several outputs at once
when run on a ReusableText input file e.g. ``lecture.rst``:

* a reST ``lecture_slides.rst`` file containing slides for
  converting via ``rst2beamer``.  ReusableText ``question``
  blocks are treated specially: one slide is generated for
  the question, followed by one slide showing the answer.
* a latex ``lecture_slides.tex`` converted by ``rst2beamer``.
* a PDF ``lecture_slides.pdf`` converted by ``pdflatex``.
* a CSV ``lecture.csv`` containing the ReusableText ``question``
  objects in a format readable by the Socraticqs in-class
  question system, for having a class of students answer
  the questions in class.

The command is run as follows::

  python /path/to/reusabletext/ctprep.py infile /path/to/socraticqs/static/images

The second argument specifies where image files used by ``image``
directives in the questions
(or answers) should be copied, so the Socraticqs web servlet will
properly serve them to web browser clients when displaying questions
or answers.


