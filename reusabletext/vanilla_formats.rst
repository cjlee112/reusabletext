:format: question

  {{ make_title(title) }}

  {{ indented('   ', this.text) }}

  {% for answer in getattr(this, 'answer', ()) %}

  {{ indented('   ', ['**Answer**:', ''] + answer) }}

  {% endfor %}

  {% for e in getattr(this, 'error', ()) %}
  {{ indented('   * ', ['**Error**:'] + e) }}
  {% endfor %}

:format: section

  {{ make_title(title, this.level) }}

  {% if getattr(this, 'conceptID', False) %}
  {% for conceptID in this.conceptID.split(',') %}
  {{ '(View Wikipedia definition: `%s <http://en.wikipedia.org/wiki/%s>`_)' % (conceptID.replace('_', ' '), conceptID) }}
  {% endfor %}
  {% endif %}

  {{ '\n'.join(this.text) }}

:format: fallacy

  {{ make_title('Fallacy: ' + title, this.level) }}

  {{ '\n'.join(this.text) }}

:format: multichoice-question

  {{ make_title(title) }}

  {{ indented('   ', this.text) }}

  {% for clines in this.multichoice[0] %}
  {{ indented('   #. ', clines) -}}
  {% endfor %}


  {% for answer in getattr(this, 'answer', ()) %}

  {{ indented('   ', ['**Answer**: option %d.' % (this.correct + 1)] + answer) }}

  {% endfor %}

  {% for e in getattr(this, 'error', ()) %}
  {{ indented('   * ', ['**Error**:'] + e) }}
  {% endfor %}

:format: multipart-question

  {{ make_title(title) }}

  {% if this.text %}
  {{ indented('   ', this.text) -}}
  {% endif %}
  {% for subq in children %}
  {{ indented('   #. ', subq.text) -}}
  {% for answer in getattr(subq, 'answer', ()) %}

  {{ indented('      ', ['**Answer**:', ''] + answer) }}

  {% endfor %}
  {% endfor %}


:format: warning

  {{ '\n' + directive('warning', '', this.text) }}

:format: comment

  {{ '\n' + directive('note', '', this.text) }}

:format: formal-definition
  
  **Formal definition**:
  {{ '\n'.join(this.text) }}
  
:format: informal-definition
  
  **Informal definition**:
  {{ '\n'.join(this.text) }}
  
:format: derivation
  
  **Derivation**:
  {{ '\n'.join(this.text) }}
  
:format: defines

  {{ indented('* ', ['**Definition**:'] + this.text) -}}
  
