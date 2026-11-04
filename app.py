from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Driving Route Planner - Project Initialized"

if __name__ == "__main__":
    app.run(debug=True)
  
