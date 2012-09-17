############################
Project Name: Reuseable Text
############################

Design Goals
------------

* keep it simple, practical.  Don't try anything that you aren't
  sure is needed.
* enable writer to split material into single-concept units that
  we want to re-use in different combinations and for different
  purposes.  E.g. a given case can be used as an illustrative
  example in a text, as a concept test, or a homework or exam
  problem.  The challenge is that once you split up the material
  like this, you need a good way to put it back together again
  to producing different outputs, e.g. a reading, a set of
  slides.  Clearly there can be different "forms" for the same
  concept, e.g. presented as text in a textbook (complete sentences,
  not limited to a short length like a slide); a slide
  (short phrases or "bullet points", strict length limit).

need to look through all my material and
categorize different types of content:

* informal definition
* formal definition
* concept test (single concept, no mechanics)
* error model or fallacy
* example that motivates introducing a concept

Meta-document: a document that includes material from many other documents

We can carve out a lot of material as single-concept units
that will be useful to re-use in many different settings.
However, there will always be "bridge" material that is custom
to a specific document, e.g. to *connect* from one piece
of inserted content to an unrelated piece of content.

For a writer there is something unnatural about splitting the
text into small "reusable" units.  Writing is about flow and linkage,
the opposite of "splitting".  I doubt people will want to write
a "database" of such snippets instead of the usual textbook
chapter as an integrated whole.
Perhaps I should focus on how to annotate an existing text,
tagging the concepts it contains, and the function of each
piece of text.


Separate problems:

* homework and exam problems: probably the most useful category
  for "reusable content tools".  Typical structure is an intro
  that sets up a problem, followed by one or more specific
  questions.  There can even be more than one layer of this.
  We need an easy syntax for selecting which problems
  and parts you want to use, and the ability to inject
  customizations.

  This takes us into the realm of namespaces.  The basic elements
  seem to be:

  * a specific source text from which we are drawing material
  * a specific concept ID, using universal identifiers (e.g. wikipedia)
    or perhaps a local identifier set (as long as it's defined and mapped
    to the universal identifiers).
  * a problem or section ID
  * subproblem or subsection IDs... however many layers you want.

  Right now, my simple code only handles single-section Question.
  I'd need to define how to extend this to subsections, subproblems.
  However, I think the basic pattern of parsing the ReST into
  a "section parse-tree" with metadata attributes makes good sense.

  Some basic principles:

  * It seems wise to write ID as a metadata tag rather than use
    the text title as the ID.  
  * Referring to an ID that has subsections includes all its
    subsections.  You only have to specify subsections if you
    want to include specific subsections and skip other subsections.
  * It should use the existing conventions of ReST as much as possible.
    For example, write a multiple choice question using the standard
    list format.
  * Following that theme, the format should aim for the same
    virtues as ReST: readability and simplicity.  There is no
    need for complex formats if we focus on the main things people
    want to do.

  How to format a content selection list, and specify output format?

  Content selection format choices:

  * add (or extend) a ReST directive?  The ``include`` directive
    is useful but quite limited.
  * some kind of simple csv format (which people would presumably
    edit in a spreadsheet)?
  
  Pipeline:

  * parsing of the source database ReST
  * content selection that can pull specified IDs from the source
  * many kinds of output channels

* slides 
  * lectures: tie audio or video to a set of slides
* textbook

Example Text Format
-------------------

:defines: something
:depends: some_other_concept

:informal-definition:
  some text

  :defines: something_else
    definitions can be nested...

:formal-definition:
  :this: subsectionName
  more text

:derivation:
  how we derive this

:comment:
  identifiers should follow Python variable name rules i.e. [A-Za-z_0-9]+
:warning:
  watch out for Jahangir!

Example Question Format
-----------------------

:tests: something

:intro:
  Four score and seven years ago...

:question: MRCAlocations
  Where were you on the night of February 30th?

  :answer:
    Right here in River City.

:question: treeConfidence
  Which of the branches in this tree appear to be confident?

  .. image:: sometree.png

  :answer:
    foobar.

  :error: nameOfError1
    some text explaining this kind of error..

  :error: nameOfError2
    more text about another kind of error...


Next Question
-------------

more of the same...

:question: myquestion
  :qtype: multichoice

  * choice 1
  * choice 2
  * choice 3
  * choice 4


Is it better to use this "implicit end" annotation model, or explicit
start-end marks as in :start-answer: :end-answer:?
HTML of course opts for the latter.  The obvious problem with
"implicit end" is that there have to be special rules for what
tags terminate other tags...  e.g. :answer: terminates :question:
but :qtype: doesn't...  Could be yucky.

Note also that this format doesn't permit nesting of subquestions
within questions.

Another possibility: use indentation, just like ReST does.  e.g.

:question: nameOfQuestion
  here is the question

  :answer:
    here is the answer.

This actually seems like a pretty robust, simple solution.

Implicit containment or association
-----------------------------------

When we supply an answer immediately after a question, of course
it should be associated with that question.  How exactly should we
implement this?  To my mind this is like "implicit containment"
in ReST (e.g. subsections); the answer block is parsed as "contained" in
the question block.  Presumably this is just a function of the
block type: the ``answer`` block only makes sense as a sub-block
of a ``question`` block.  We could implement this by keeping
a dictionary of which types of blocks expect to be sub-blocks of
some other kind of block.


Association with multiple concepts
----------------------------------

So far I've assumed a question tests just *one* concept.  That
seems overly simplistic, but making things complicated won't
necessarily be better.  Of course a given question will depend
on understanding multiple concepts.  But we'd be nuts to 
exhaustively annotate all the concepts that it depends on...
that is almost infinite regress.  Instead we annotate what
concept it is *intended* to test.  A concept test should focus
on testing only one concept.  Synthesis questions can certainly
test the ability to use multiple concepts together...
It seems fine to allow a question to test more than one
concept, and to be able to refer to that question via any
of the concepts that it tests.

Puzzle: metadata vs. list?
--------------------------

E.g. to write a multiple choice question, we could follow two
different approaches: use metadata to mark the parts, or the
intuitive ReST list:

metadata:

:question: nameOfQuestion
  text that asks the question
  :multiple-choice: first option
  :multiple-choice: second option
  :multiple-choice: third option :correct:
  :multiple-choice: fourth option

ReST list:

:question: nameOfQuestion
  text that asks the question

  * first option
  * second option
  * third option :correct:
  * fourth option

A hybrid model:

:question: nameOfQuestion
  text that asks the question
:multiple-choice:
  * first option
  * second option
  * third option :correct:
  * fourth option

I like the hybrid model.  The principle is clear: we stick with
the simplicity and consistency of ReST wherever practical, but
we add a little "salt" (metadata) to make explicit *what* each
piece of text is.  It also nicely separates the question from
the form of the answer; e.g. we could ask this question either
as multiple choice or as open-response.


What must the content-selection format do?
------------------------------------------

* specify content to select
* provide control over structure: let me insert one piece of
  content in another.  This can easily be done with a ReST list structure.
* specify output format: there are lots of variables we might
  want here, e.g. inserting raw latex for space in a printed exam.
  Consider using jinja2 templates?

* default: if no subcontent specified, insert as-is.  If subcontent 
  specified, just insert that specified subset.


.. select:: path/to/source

   * conceptID.nameOfQuestion
     :format:
       #. **{{- title -}}**

     * intro
     * INSERT Whatever other text I want, right in the middle...
     * firstPart
       :vspace: 6cm
     * secondPart

Questions

* I want this to work recursively, i.e. to be able to select
  from RUsT that itself constructs ReST using select.
  For example, I build slides using select from source RUsT.
  Then I build a slide show by pulling the slides I want.

* how to specify an absolute path within this local context?
  Choices:

  * local context must be specified, e.g. _.intro instead of just intro
  * use some kind of first character for specifying absolute path, 
    e.g. / or : or + or $ or @
    Seems like / should be reserved for file paths.
    $someConcept.shortDefinition ... not completely horrible.
  * use some keyword to indicate an absolute path, e.g. PATH or CONCEPT
  * treat the initial select as an "import" into the namespace,
    and treat each section as a "local scope" that *adds* the
    symbols contained in that specified section.
    This can all be recursive.  I.e. follow the Python model, where
    a sub-scope sees all the symbols in the surrounding scope
    as well as its own symbols.  The only problem arises when
    a local symbol has the same name as a symbol from the surrounding
    context.

    This is appealing.  I don't want to clutter the 
    syntax with funny symbols or keywords.

Concept path spec:  you could specify an absolute path as

``path/to/source:conceptID.intro``

Is there an advantage to importing a whole "module" (a directory
containing many files) vs. a specific file.  Easy to allow
users to specify either a file or a directory, and act 
accordingly.

Handling "This"
---------------

When we write a text, we use the word "this" to refer to
a previous item, implicitly.  If you take a piece of text out
of context, the reader has no way of knowing what "this" refers
to.  So we need to tag that information explicitly.  We can
adopt the following rule:

* by default, "this" is assumed to refer to (something in) the
  previous subsection.
* to override that default, you must provide a :this: tag giving
  the identifier it refers to.  It could be a concept ID,
  subsection identifier, equation label, figure, etc.


Principles
----------

* the goal is to annotate normal textbook writing rather than force
  people to rewrite existing text or learn a completely different
  way of writing.
* the method is to follow ReStructured Text's simple patterns,
  e.g. indentation to indicate subsections, while making the
  implicit structure of the text *explicit* through metadata tags.
  In particular:

  * metadata values in the usual ReST way,
    e.g. as used in directive parameters.
  * metadata blocks: an indented block of content under a metadata
    header.  This is clearer and more general than trying to make
    every block a ReST section.  Since the metadata structure is
    mostly flat, deep nesting is unlikely, so indentation will not
    be unduly irksome.
  * metadata tags that "attach" to the enclosing section should
    generally be *verbs* (predicates) such as :defines:, :depends:.
    This convention indicates that the "subject" of the predicate 
    precedes it, i.e. is the enclosing scope.
  * metadata tags that "attach" to their enclosed content should
    generally be *nouns* such as :question:, :informal-definition:
    etc.  This rule clearly distinguishes whether a given tag expects
    enclosed content or not.
* make concepts and connections explicit by inserting metadata, as
  I worked out in my original annotation proposal last fall.
  More features such as :this: can be added as needed.
* create a convenient namespace for selecting content, consisting of
  *module path*; *concept ID*; *block ID*.

  * module path: a convenient way of selecting a content source,
    typically somebody's textbook.
  * concept ID: a flat, universal namespace (i.e. Wikipedia), or 
    if desired a local namespace defined by a content source
    (ideally with a mapping to the universal namespace).
  * block ID: each block should have an identifier (name that is
    unique within its containing block) so we can easily refer to it.


What to work on first
---------------------

* slides: probably the easiest category, because slides are natural
  "units" already.  All we need to do is annotate them appropriately
  for easy selection.
* questions & answers: a bit more challenging, since we want to 
  produce many different output formats (homework, exams, slides,
  csv etc.), and we often need to splice various bits and pieces
  together.
* textbook: more challenging, because we are dissecting a complex
  flow of text in component parts that can be reused.  This will
  take more thought and work to make a usable system.


The Tool Components
-------------------

* content parser: need a tool that reads ReST with metadata,
  and returns a "parse tree" and index of the namespace.

  * basic parse tree split into sections, with subsections within
    sections.  If a section has no subsections, then its contents
    simply stored in ``text`` attribute.  Any subsections are
    appended as its ``list`` (which can be empty).
  * metadata blocks operate in exactly the same manner, except
    that some blocks implicitly "bind" within the previous block
    e.g. :answer: block binds within preceeding :question: block.
  * named blocks get registered in a dictionary on the containing
    block.  We can also have an attribute named for the subblock
    type e.g. ``questions``, which would be a dictionary of 
    questions within that block.
  * regular metadata values just get stored as attributes on
    the block they're in.  
  * block types: we can define many different types of blocks,
    e.g. multiple choice question could interpret list items as
    the multiple choice answers.
  * such block parsing is an *extension*: the raw text of the block
    is always available as attribute ``text``, but the block parser
    can add extra attributes that any output formatter can use if desired.

Selection re-formatting
-----------------------

General model: selection constructs a dictionary of source content, 
and passes that to a specified template.

Source content should have standard format:

ID
[ID1, ID2]
(var1=EXPR, var2=EXPR)







    
