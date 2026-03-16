import google.genai as g

client = g.Client(api_key='test')
# Use the interactions create signature but don't actually call API
# Instead, inspect the return type from the type hints in the method signature
from inspect import signature

sig = signature(client.interactions.create)
print('signature:', sig)
print('return annotation:', sig.return_annotation)
