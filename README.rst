
What is ReusableText?
---------------------

`ReusableText <http://people.mbi.ucla.edu/leec/docs/reusabletext/>`_
is a minor but very useful extension of 
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

