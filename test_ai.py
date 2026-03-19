import google.generativeai as genai

# Configure with your API key
genai.configure(api_key="AIzaSyCEq7nuMsg0MbOz4mqawG1YB0EoOQT5FH8")

# Get the model
model = genai.GenerativeModel('gemini-2.0-flash')

# Generate content
response = model.generate_content("Say 'Hello World' in one word")
print("✅ SUCCESS:", response.text)