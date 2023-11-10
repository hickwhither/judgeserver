from flask import Flask, request

import requests
import threading, time, os, shutil
import judge
import random, string, sys
import time


from dotenv import load_dotenv
env = load_dotenv()

AUTHORIZATION = env['AUTHORIZATION']

app = Flask(__name__)


# def gogo(kwargs):
#     try:
#         data = judge.judge(**kwargs)
#     except Exception as e:
#         data = {"result": "error"}
#     requests.post(MAIN_URL, headers=headers, data=data)

@app.route('/status', methods=["GET"])
def status():
    if AUTHORIZATION == None or request.headers.get('authorization') != AUTHORIZATION:
        return {"response": "au1thorization not matched"}
    return {"response": "success", "uptime":starttime,"languages": judge.status()}


@app.route('/func/<string:func>', methods = ["POST"])
def funcs(func):
    if AUTHORIZATION == None or request.headers.get('authorization') != AUTHORIZATION:
        return {"response": "au1thorization not matched"}
    form = dict((key, request.form.getlist(key) if len(request.form.getlist(key)) > 1 else request.form.getlist(key)[0]) for key in request.form.keys())
    data = eval(f"judge.{func}(**form)", globals(), locals())
    return {"response": "success", "data": data}


if __name__ == '__main__':
    if not os.path.exists('./tmp'): os.mkdir('./tmp')
    starttime = time.time()
    app.run()

