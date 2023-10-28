from flask import Flask, request

import requests
import threading, time, os, shutil
import judge
import random, string, sys

# from dotenv import load_dotenv
# load_dotenv()

AUTHORIZATION = sys.argv[3]
MAIN_URL = sys.argv[4]

app = Flask(__name__)

def hello(*args, **kwargs):
    try:
        winner, response = judge.fighting(**kwargs)
    except Exception as e:
        winner, response = (-1, e)
    headers = {"authorization": AUTHORIZATION}
    data = {"winner": winner, "response": response}
    requests.post(MAIN_URL, headers=headers, data=data)
    

@app.route('/botfight', methods = ["POST"])
def botfight():
    if AUTHORIZATION == None or request.headers.get('authorization') != AUTHORIZATION:
        return {"response": "authorization not matched"}

    try:
        winner, response = judge.fighting(**request.form)
    except Exception as e: winner, response = (-1, str(e))
    
    data = {"winner": winner, "response": response}
    return data


if __name__ == '__main__':
    if not os.path.exists('./tmp'): os.mkdir('./tmp')
    app.run(host=sys.argv[1], port=sys.argv[2])

