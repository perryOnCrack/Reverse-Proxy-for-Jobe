from flask import Flask

app = Flask(__name__)

@app.route('/settings')
def settings():
    pass