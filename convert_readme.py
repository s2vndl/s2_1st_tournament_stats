import markdown

mkin = open("index.md")
md = markdown.Markdown(extensions=['toc', 'codehilite', 'meta'], output_format="html")
gen_html = md.convert(mkin.read())
title = "s2stats"

output = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <link href="static/markdown.css" type="text/css" rel="stylesheet" />
    <title>{title}</title>
  </head>
<body>
{gen_html}
</body>
</html>
"""

print(output)
outfile = open("markdown/index.html", 'w')
outfile.write(output)
outfile.close()