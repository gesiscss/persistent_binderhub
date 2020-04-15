<html>
<body>

<p>See installation instructions at <a href="https://github.com/gesiscss/persistent_binderhub">Persistent BinderHub</a></p>

<h2>Releases</h2>
{% assign all_charts = site.index.entries.persistent_binderhub | sort: 'created' | reverse %}
<table>
  <tr>
    <th>release</th>
    <th>date</th>
  </tr>
  {% for chart in all_charts %}
    <tr>
      <td>
      <a href="{{ chart.urls[0] }}">
          {{ chart.name }}-{{ chart.version }}
      </a>
      </td>
      <td>
      <span class='date'>{{ chart.created | date_to_rfc822 }}</span>
      </td>
    </tr>
  {% endfor %}
</table>
</body>
</html>
