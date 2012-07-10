
:format: multipart-question
  {{ indented('#. ', this.text) }}

  {% for subq in children %}

  {{ indented('   #. ', subq.text) }}

  {% if insertPagebreak %}
  {{ indented('      ', directive('raw', 'latex', '\\pagebreak')) }}
  {% elif insertVspace %}
  {{ indented('      ', directive('raw', 'latex', '\\vspace{%s}' % insertVspace)) }}
  {% endif %}

  {% endfor %}
