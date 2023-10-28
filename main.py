from flask import Flask, request

import requests
import threading, time, os, shutil
import judge
import random, string

from dotenv import load_dotenv
load_dotenv()

AUTHORIZATION = os.getenv('AUTHORIZATION')
MAIN_URL = os.getenv('MAIN_URL')

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
    if request.headers.get('authorization') != AUTHORIZATION:
        return {"response": "authorization not matched"}

    try:
        winner, response = judge.fighting(**request.form)
    except Exception as e: winner, response = (-1, str(e))
    
    data = {"winner": winner, "response": response}
    return data


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3272)

