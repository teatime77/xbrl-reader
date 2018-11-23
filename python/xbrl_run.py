import os
import time
from pathlib import Path
import multiprocessing
import json
import codecs
from multiprocessing import Process, Array
from xbrl_reader import readXbrlThread, make_public_docs_list

start_time = time.time()

def f(cpu_count, cpu_id, public_docs_list, progress):

    readXbrlThread(cpu_count, cpu_id, public_docs_list, progress)

if __name__ == '__main__':

    cpu_count = multiprocessing.cpu_count()

    progress = Array('i', [0] * cpu_count)
    public_docs_list = make_public_docs_list(cpu_count)

    process_list = []
    for cpu_id in range(cpu_count):

        p = Process(target=f, args=(cpu_count, cpu_id, public_docs_list[cpu_id], progress))

        process_list.append(p)

        p.start()


    for p in process_list:
        p.join()    

    print('終了:%d' % int(time.time() - start_time) )
