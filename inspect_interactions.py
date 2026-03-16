import google.genai as g
import inspect

client = g.Client(api_key='test')
inter = client.interactions
print('interactions object type:', type(inter))

cls = inter.__class__
print('class:', cls)

src = inspect.getsource(cls)
print(src[:3000])
