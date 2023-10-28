import random
import os, json, tempfile, shutil
import threading, subprocess, time, signal
from interactor import create_subprc
# from distutils.dir_util import copy_tree
# from shutil import copyfile

languages = {}


for _ in os.listdir('languages'):
    if os.path.isdir(_): continue
    if not _.endswith('.json'): continue
    with open(f"languages/{_}") as f:
        languages[_[:-5]] = json.load(f)


def compilebot(langg, tempfolder, source, botname):
    lang = languages.get(langg)
    name = os.path.join(tempfolder, botname)
    file1 = name + '.'+ langg
    with open(file1, "w", encoding="utf-8") as f: f.write(source)
    compiling = create_subprc(lang['terminal'].format(name=name,file=file1))
    compiling.communicate()
    return compiling, lang['executable_file'].format(name=name,file=file1)


def fighting(bot1lang, bot1source, bot2lang, bot2source, source, *args, **kwargs) -> tuple:
    """
    (Winner, Response)
    
    `-1` -> Interactor error
    
    `0` -> Draw
    
    `1` -> Bot1 wins
    
    `2` -> Bot2 wins
    """
    tp = tempfile.TemporaryDirectory(prefix="TCOJbattlebot_", dir='./tmp/')
    tempfolder = tp.name


    # Compile bot
    compiling1, exefile1 = compilebot(bot1lang, tempfolder, bot1source, "bot1")
    compiling2, exefile2 = compilebot(bot2lang, tempfolder, bot2source, "bot1")

    # Fail

    if compiling1.subprc.returncode!=0 or compiling2.subprc.returncode !=0:
        if compiling1.subprc.returncode!=0 and compiling2.subprc.returncode!=0:
            return (0, "Both compiler error")
        elif compiling1.subprc.returncode!=0:
            return (2, "Bot1 compiler error")
        else:
            return (1, "Bot2 Compiler error")
    
    # Interactor shows up >;)
    bot1 = create_subprc(exefile1)
    bot2 = create_subprc(exefile2)
    
    try:
        exec(source, locals())
        res = locals()['judge'](bot1, bot2)
        if type(res) != tuple: raise Exception("Interactor return error")
        if res[0] not in [0, 1, 2]: raise Exception(f"Interactor return `{res[0]}` instead of win number")
    except Exception as e:
        res = (-1, str(e))
    
    bot1.terminate()
    bot2.terminate()

    return res