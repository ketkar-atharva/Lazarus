import google.genai as g
import inspect

src = inspect.getsource(g.Client)
for line in src.splitlines():
    if 'def ' in line and ('generate' in line or 'completion' in line or 'create' in line):
        print(line)
