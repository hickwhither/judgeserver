import random
import os, json, tempfile, shutil
import threading, subprocess, time, signal, asyncio
import compileall

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
    try: subprocess.check_output(lang['terminal'].format(name=codename),cwd=dname, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e: #Fail
        return '', e
    exefile = lang['executable_file'].format(name=codename)

    popen = subprocess.Popen(exefile,cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    try: data = popen.communicate(stdin.encode(), timeout = 10)
    except subprocess.TimeoutExpired: return '', 'killed'
    return data[0].decode(), data[1].decode()



async def ajudge(dname, exefile, generatorrun, timelimit, **kwargs):
    
    async def single(i, cline):
        global maxtime
        genp = subprocess.Popen('eva.exe',cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdin = genp.communicate(timeout = timelimit)[0]
        exepopen = subprocess.Popen(exefile,cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        starttime = time.time()
        try: stdout, stderr = exepopen.communicate(stdin, timeout = timelimit)
        except subprocess.TimeoutExpired:
            result[i] = (None, '', '', '', '', timelimit)
            return
        timedelta = time.time() - starttime
        stdin = stdin.decode()
        stdout = stdout.decode()
        stderr = stderr.decode()

        if exepopen.returncode:
            result[i] = (None, exepopen.stderr)
            return

        with open(os.path.join(dname,'stdin.txt'), 'w') as f: f.write(stdin)
        with open(os.path.join(dname,'stdout.txt'), 'w') as f: f.write(stdout)
        evap = subprocess.Popen('eva.exe',cwd=dname,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        pin, perr = evap.communicate(timeout = timelimit)
        pin = pin.decode()
        perr = perr.decode()
        
        result[i] = pin, perr, stdin, stdout, stderr, timedelta

    timelimit = float(timelimit)
    maxtime = 0.0
    
    result = [None for i in range(len(generatorrun))]

    asyncio.gather(*[single(i, generatorrun[i]) for i in range(len(generatorrun))])

    # for i in result:

    return result, maxtime




def judge(code, lang, generator, generatorrun, evaluator, timelimit, **kwargs):
    """
    - list [(evaluate, evaluator_response, stdin, stdout, stderr, time)]
    - Compiler status
    - Max time
    """
    lang = languages[lang]
    
    # Creating tempdict
    td = tempfile.TemporaryDirectory(prefix="judgeserver_")
    dname = td.name
    codename = os.path.join(dname, "main")

    ### Usercode ###
    with open(lang['file'].format(name=codename), 'w', encoding="utf-8")as f:
        f.write(code)
    try: subprocess.check_output(lang['terminal'].format(name=codename),cwd=dname, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e: #Fail
        return [], f"Returned as {e.returncode}\n---\n{e.output.decode()}\n---", '_', dname
    
    exefile = lang['executable_file'].format(name=codename)

    shutil.copy2("./testlib.h", os.path.join(dname,"testlib.h"))
    ### Generator ###
    with open(os.path.join(dname, "gen.cpp"), 'w', encoding="utf-8")as f:
        f.write(generator)
    try: subprocess.check_output("g++ --std=c++17 gen.cpp -o gen.exe", cwd=dname, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e: #Fail
        return [], f"Generator Failed\nReturned as {e.returncode}\n---\n{e.output.decode()}\n---", '_', dname

    ### Evaluator ###
    with open(os.path.join(dname, "eva.cpp"), 'w', encoding="utf-8")as f:
        f.write(evaluator)
    try: subprocess.check_output("g++ --std=c++17 eva.cpp -o eva.exe", cwd=dname, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e: #Fail
        return [], f"Evaluator Failed\nReturned as {e.returncode}\n---\n{e.output.decode()}\n---", '_', dname
    

    res = asyncio.run(ajudge(dname, exefile, generatorrun, timelimit))

    return res[0], "", res[1], dname
    
