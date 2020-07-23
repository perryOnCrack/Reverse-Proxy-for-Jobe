import os
import sys
import json
import time
from flask import Flask, jsonify

# Some constants
PATH_working_server = 'working_server.json'
PATH_joeb_list = 'jobe_list.json'
PATH_sorted_lang = 'sorted_lang.json'
TBE = sys.maxsize # Time Before Expired

app = Flask(__name__)



@app.route('/languages')
def languages():
    # Check working_server.json's mod time to determent 
    # if we need to generate new one or using existing sorted_lang.json.
    # If the file is not there, generate new one.
    if os.path.exists(PATH_working_server) and ((time.time() - os.path.getmtime(PATH_working_server)) < TBE):
        try:
            with open(PATH_sorted_lang, 'r') as f:
                return jsonify(json.loads(f.read()))
        except:
            print('ERROR: Failed reading "' + PATH_working_server + '"')
    
    # Generate new working_server.json.
    # Return empty if any thing goes wrong from this point forward
    # First we read in jobe_list.json

if __name__ == '__main__':
    app.run()
