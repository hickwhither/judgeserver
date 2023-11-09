import random
import os, json, tempfile, shutil
import threading, subprocess, time, signal, asyncio

languages = {}


for _ in os.listdir('languages'):
    if os.path.isdir(_): continue
    if not _.endswith('.json'): continue
    with open(f"languages/{_}") as f:
        languages[_[:-5]] = json.load(f)


def status():
    return list(languages.keys())


def compile(code, lang, stdin):
    lang = languages[lang]
    
    # Creating tempdict
    td = tempfile.TemporaryDirectory(prefix="judgeserver_")
    dname = td.name
    codename = os.path.join(dname, "main")

    ### Usercode ###
    with open(lang['file'].format(name=codename), 'w', encoding="utf-8")as f:
        f.write(code)
    try: subprocess.run(lang['terminal'])
    except subprocess.CalledProcessError as e: #Fail
        return '', e
    exefile = lang['executable_file'].format(name=codename)

    popen = subprocess.Popen(exefile,cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try: data = popen.communicate(bytes(stdin), timeout = 10)
    except subprocess.TimeoutExpired: return '', 'killed'
    return data[0].decode(), data[1].decode()



async def ajudge(dname, exefile, generatorrun, timelimit):
    
    maxtime = 0.0

    result = [None for i in range(len(generatorrun))]
    generatorrun = generatorrun.strip().split('\n')

    async def single(i, cline):
        try: stdin = subprocess.check_output(cline, cwd=dname)
        except subprocess.CalledProcessError as e:
            result[i] = (None, e)
            return
        
        exepopen = subprocess.Popen(exefile,cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        starttime = time.time()
        try: stdout, stderr = exepopen.communicate(bytes(stdin), timeout = timelimit)
        except subprocess.TimeoutExpired:
            result[i] = (None, '', '', '', '', timelimit)
            return
        timedelta = time.time() - starttime
        stdout = stdout.decode()
        stderr = stderr.decode()
        maxtime = max(maxtime, timedelta)

        if exepopen.returncode:
            result[i] = (None, exepopen.stderr)
            return

        with open(os.path.join(dname,'stdin.txt'), 'w') as f: f.write(stdin)
        with open(os.path.join(dname,'stdout.txt'), 'w') as f: f.write(stdout)
        p = subprocess.Popen('eva.exe',cwd=dname)
        pin, perr = p.communicate(timeout=10)
        pin = pin.decode()
        perr = perr.decode()
        
        result[i] = pin, perr, stdin, stdout, stderr, timedelta

    asyncio.gather(*[single(i, generatorrun[i]) for i in range(len(generatorrun))])

    return result, maxtime




def judge(code, lang, generator, generatorrun, evaluator, timelimit):
    """
    - list [(evaluate, evaluator_response, stdin, stdout, stderr, time)]
    - Compiler status
    - Max time
    """
    lang = languages[lang]
    
    # Creating tempdict
    td = tempfile.TemporaryDirectory(prefix="judgeserver_")
    dname = td.name

    ### Usercode ###
    with open(os.path.join(dname, lang['file']), 'w', encoding="utf-8")as f:
        f.write(code)
    try: subprocess.run(lang['terminal'], cwd=dname)
    except subprocess.CalledProcessError as e: #Fail
        return [], f"Returned as {e.returncode}---\n{e.output}---\n{e.stderr}"
    
    exefile = lang['executable_file']
    
    ### Generator ###
    with open(os.path.join(dname, "gen.cpp"), 'w', encoding="utf-8")as f:
        f.write(generator)
    try: subprocess.run("g++ --std=c++17 gen.cpp -o gen.exe", cwd=dname)
    except subprocess.CalledProcessError as e: #Fail
        return [], f"Generator Failed\nReturned as {e.returncode}---\n{e.output}---\n{e.stderr}"

    ### Evaluator ###
    with open(os.path.join(dname, "eva.cpp"), 'w', encoding="utf-8")as f:
        f.write(evaluator)
    try: subprocess.run("g++ --std=c++17 eva.cpp -o eva.exe", cwd=dname)
    except subprocess.CalledProcessError: #Fail
        return [], f"Evaluator Failed\nReturned as {e.returncode}---\n{e.output}---\n{e.stderr}"
    
    res = asyncio.run(ajudge(dname, exefile, generatorrun, timelimit))
    return res[0], "", res[1]
    
