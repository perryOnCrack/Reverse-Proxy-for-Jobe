import os

from flask import Flask, json, jsonify


from flask import Flask
app = Flask(__name__)


@app.route('/jobe/index.php/restapi/languages')
def languages():
    # Check working_server.json's mod time to determent if we need to generate new one
    try:
        with open('working_server.json', 'r'):
            

    return ret

if __name__ == '__main__':
    app.run()
