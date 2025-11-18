'''
#!/usr/bin/env python3
import sys
import json
import requests
from icecream import ic

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_prompt.py 'your prompt here' [output_file.py]")
        sys.exit(1)

    prompt = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "code/output.py"

    ic(prompt)
    ic(output_file)

    url = "http://31.97.146.63:11444/api/generate"
    payload = {
        "model": "codellama:latest",
        "prompt": prompt,
        "options": {
            "temperature": 0
        },
        "stream": False
    }

    headers = {"Content-Type": "application/json"}
    ic("Sending request...")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        generated_code = result.get("response", "")

        if not generated_code.strip():
            print("⚠️ No code returned by the model.")
            return

        # Save code to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generated_code)

        ic(f"✅ Code saved to {output_file}")
        print(f"Code saved to {output_file}")
    except Exception as e:
        ic(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
-----------  run the code ----------------
python codelama_code.py "create a basic Python Flask Application"
ic| prompt: 'create a basic Python Flask Application'
ic| output_file: 'code/output.py'
ic| 'Sending request...'
ic| f"✅ Code saved to {output_file}": '✅ Code saved to code/output.py'
Code saved to code/output.py



To create a basic Python Flask application, you can follow these steps:

1. Install Flask by running the following command in your terminal or command prompt:
```
pip install flask
```
2. Create a new file called `app.py` and add the following code to it:
```
'''
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
'''
```
3. Save the file and run it by typing `python app.py` in your terminal or command prompt. This will start the Flask development server and you should be able to access your application at <http://localhost:5000/>.
4. To add more routes to your application, you can use the `@app.route()` decorator to define a new function for each route. For example:
```
@app.route("/users")
def users():
    return "Users"

@app.route("/about")
def about():
    return "About"
```
5. To handle HTTP methods like GET, POST, PUT, and DELETE, you can use the `methods` parameter of the `@app.route()` decorator. For example:
```
@app.route("/users", methods=["GET"])
def get_users():
    return "Get users"

@app.route("/users", methods=["POST"])
def create_user():
    return "Create user"

@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):
    return "Update user"

@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):
    return "Delete user"
```
6. To handle errors and exceptions, you can use the `try`/`except` block in your route functions. For example:
```
@app.route("/users")
def users():
    try:
        # do something that might raise an error
    except Exception as e:
        return "Error: {}".format(e)
```
7. To deploy your application to a production environment, you can use a web server like Apache or Nginx in front of the Flask development server. You can also use a containerization technology like Docker to package your application and its dependencies into a single container that can be deployed on a cloud platform or on-premises.

That's it! With these steps, you should have a basic understanding of how to create a Python Flask application and deploy it to a production environment.
'''