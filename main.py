from flask import Flask, jsonify, request
from container_runner import runner
import json

app = Flask(__name__)

@app.route("/")
def proxy():
    response_text = runner.redirect_request(request=request)
    return jsonify(json.loads(response_text))

app.run(host='0.0.0.0', port=5000, debug=False)
