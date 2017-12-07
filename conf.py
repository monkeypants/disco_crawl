extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.viewcode',
              'sphinx.ext.graphviz']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'Disco Crawl'
copyright = '2017, Commonwealth of Australia'
author = 'Nigel O\'Keefe, Chris Gough'
version = '2.0'
release = '2.0.0'
language = None
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']
pygments_style = 'sphinx'
todo_include_todos = False
html_theme = 'alabaster'
html_static_path = ['_static']
html_sidebars = {
    '**': [
        'navigation.html',
        'searchbox.html',
    ]
}
htmlhelp_basename = 'DiscoCrawldoc'
latex_elements = {
    'papersize': 's4paper',
}
latex_documents = [
    (master_doc, 'DiscoCrawl.tex', 'Disco Crawl Documentation',
     'Nigel O\'Keefe, Chris Gough', 'manual'),
]
man_pages = [
    (master_doc, 'discocrawl', 'Disco Crawl Documentation',
     [author], 1)
]
texinfo_documents = [
    (master_doc, 'DiscoCrawl', 'Disco Crawl Documentation',
     author, 'DiscoCrawl', 'One line description of project.',
     'Miscellaneous'),
]
