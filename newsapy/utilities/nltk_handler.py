import nltk
import os
import platform

from newsapy.const import TAGGERS

def initialize_nltk_data():
    if os.path.exists("init"):
       with open("init", "r") as f:
           if f.read() != "{}".format(TAGGERS): # if were using an old tagger
               one_time_initialize() # update it
    else: # if we dont have a tagger installed at all
        one_time_initialize() # install it

def one_time_initialize():
    if platform.system() == "Darwin": # Darwin == MacOSX, for historical reasons
        python_ver = platform.python_version()[:3] # python_version() returns 3.7.2, we get 3.7
        os.system("/Applications/'Python {}'/'Install Certificates.command'".format(python_ver))
    for tagger in TAGGERS:
        nltk.download(tagger)
    with open("init", "w+") as f:
        f.write("{}".format(TAGGERS))