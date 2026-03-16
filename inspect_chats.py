import google.genai as g
import inspect

client = g.Client(api_key='test')
chats = client.chats
print('chats type:', type(chats))
print('methods:', [m for m in dir(chats) if not m.startswith('_')][:40])
print('\n--- create signature ---')
from inspect import signature
print(signature(chats.create))
