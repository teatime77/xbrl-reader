import os
import time
from pathlib import Path
import multiprocessing
import json
import codecs
import pickle
from multiprocessing import Process, Array
from xbrl_reader import Inf, SchemaElement, Calc, init_xbrl_reader, read_company_dic, readXbrlThread, make_public_docs_list

start_time = time.time()

def f(cpu_count, cpu_id, public_docs_list, progress, company_dic):

    readXbrlThread(cpu_count, cpu_id, public_docs_list, progress, company_dic)

if __name__ == '__main__':

    init_xbrl_reader()
    company_dic = read_company_dic()

    cpu_count = multiprocessing.cpu_count()

    progress = Array('i', [0] * cpu_count)
    public_docs_list = make_public_docs_list(cpu_count, company_dic)

    process_list = []
    for cpu_id in range(cpu_count):

        p = Process(target=readXbrlThread, args=(cpu_count, cpu_id, public_docs_list[cpu_id], progress, company_dic))

        process_list.append(p)

        p.start()


    for p in process_list:
        p.join()    

    print('終了:%d' % int(time.time() - start_time) )
