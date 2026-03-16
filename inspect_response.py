import os
from dotenv import load_dotenv
import google.genai as g

load_dotenv()

key = os.environ.get('GEMINI_API_KEY')
print('GEMINI_API_KEY set?', bool(key))
client = g.Client(api_key=key)
resp = client.interactions.create(model='gemini-2.5-flash-lite', input='Test prompt: say hello.')
print('Response type:', type(resp))
print('outputs type:', type(resp.outputs))
print('outputs length:', len(resp.outputs) if resp.outputs else 0)
if resp.outputs:
    first = resp.outputs[0]
    print('first output type:', type(first))
    print('first output fields:', [f for f in dir(first) if not f.startswith('_')][:40])
    # attempt to print possible text content
    if hasattr(first, 'text'):
        print('text field:', first.text)
    if hasattr(first, 'summary'):
        print('summary field:', first.summary)
    if hasattr(first, 'thoughts'):
        print('thoughts:', first.thoughts)
    if hasattr(first, 'signature'):
        print('signature:', first.signature)
print('raw repr:', resp)
