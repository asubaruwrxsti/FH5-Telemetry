import flask

webservice_port = 5000

app = flask.Flask(__name__)
app.run(host='localhost', port=webservice_port)

@app.route('/data', methods=['POST'])
def data():
    return flask.request.get_json()

@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html', data=data)
