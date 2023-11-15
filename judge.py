import random
import os, json, tempfile, shutil
import threading, subprocess, time, signal, asyncio
import compileall

def addtestlib(app, *args, **kwargs):
    shutil.copy2("./testlib.h", os.path.join(app.dname,"testlib.h"))

languages = {}


for _ in os.listdir('languages'):
    if os.path.isdir(_): continue
    if not _.endswith('.json'): continue
    with open(f"languages/{_}") as f:
        languages[_[:-5]] = json.load(f)


def status():
    return list(languages.keys())


def compile(code, lang, stdin, **kwargs):
    lang = languages[lang]
    
    # Creating tempdict
    td = tempfile.TemporaryDirectory(prefix="judgeserver_")
    dname = td.name
    codename = os.path.join(dname, "main")

    ### Usercode ###
    with open(lang['file'].format(name=codename), 'w', encoding="utf-8")as f:
        f.write(code)
    try: subprocess.check_output(lang['terminal'].format(name=codename),cwd=dname, stderr=subprocess.STDOUT,shell=True)
    except subprocess.CalledProcessError as e: #Fail
        return '', f"Returned as {e.returncode}\n---\n{e.output.decode()}\n---"
    exefile = lang['executable_file'].format(name=codename)

    popen = subprocess.Popen(exefile,cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    try: data = popen.communicate(stdin.encode(), timeout = 10)
    except subprocess.TimeoutExpired: return '', 'killed'
    return data[0].decode(), data[1].decode()


class Appcompile:
    def __init__(self, source: str, language: str, **kwargs):
        language = languages[language]

        self.td = tempfile.TemporaryDirectory(prefix="tcojjudge_")
        self.dname = self.td.name
        codename = os.path.join(self.dname, "main")

        with open(language['file'].format(name=codename), 'w', encoding="utf-8")as f:
            f.write(source)
        
        if kwargs.get("before_compile"):
            for i in kwargs['before_compile']:
                i(self)
        
        try: subprocess.check_output(language['terminal'].format(name=codename),cwd=self.dname,stderr=subprocess.STDOUT,shell=True)
        except subprocess.CalledProcessError as e: #Fail
            self.compile = e.returncode, e.output.decode()
        else:
            self.exefile = language['executable_file'].format(name= codename)
            self.compile = 0, "Success"

    def communicate(self, stdin: str, timeout = None):
        exepopen = subprocess.Popen(self.exefile,cwd=self.dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        if timeout:
            starttime = time.time()
            stdout, stderr = exepopen.communicate(stdin.encode(), timeout = timeout)
            timedelta = time.time() - starttime
            return stdout.decode(), stderr.decode(), timedelta
        else:
            stdout, stderr = exepopen.communicate(stdin.encode())
            return stdout.decode(), stderr.decode()


def ajudge(user: Appcompile, evaluator: Appcompile, inputs, timelimit, **kwargs):


    def single(stdin):
        starttime = time.time()
        try:
            stdout, stderr, timedelta = user.communicate(stdin, timeout = timelimit)
        except subprocess.TimeoutExpired:
            return (0, 'Time Limit Exceeded', timelimit)
        else:
            evares, evaerr = evaluator.communicate(f"{stdin}\n{stdout}")
            return evares, evaerr, timedelta

    
    timelimit = float(timelimit)
    result = [single(i) for i in inputs]
    maxtime = max(i[2] for i in result)

    return result, maxtime


def judge(code, lang, evaluator, evaluatorlang, inputs, timelimit, **kwargs):
    """
    - list [(evaluate, evaluator_response, time)]
    - Compiler status
    - Max time
    """
    
    user = Appcompile(code, lang)
    if user.compile[0]: #fail
        return [], f"Compiler Failed\nReturned as {user.compile[0]}\n---\n{user.compile[1]}\n---", 0
    evaluator = Appcompile(evaluator, evaluatorlang, before_compile = [addtestlib])
    if evaluator.compile[0]:
        return [], f"Evaluator Failed\nReturned as {evaluator.compile[0]}\n---\n{evaluator.compile[1]}\n---", 0
    
    
    res = ajudge(user, evaluator, inputs, timelimit)
    
    return res[0], "", res[1]
    
