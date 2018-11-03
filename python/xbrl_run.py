import os
import time
import re
from pathlib import Path
import multiprocessing
import json
import codecs

from multiprocessing import Process, Array

start_time = time.time()

root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'
report_path = root_dir + '/data/EDINET/四半期報告書'

def make_public_docs_list(cpu_count):
    category_edinet_codes = []

    public_docs_list = [ [] for i in range(cpu_count) ]
    for category_dir in Path(report_path).glob("*"):
        category_name = os.path.basename(str(category_dir))

        edinet_codes = []
        category_edinet_codes.append( { 'category_name': category_name, 'edinet_codes': edinet_codes}   )

        for public_doc in category_dir.glob("*/*/XBRL/PublicDoc"):
            xbrl_path_list = list(public_doc.glob('jpcrp*.xbrl'))
            assert len(xbrl_path_list) == 1

            xbrl_path = xbrl_path_list[0]
            xbrl_basename = os.path.basename(str(xbrl_path))
            items = re.split('[-_]', xbrl_basename)
            edinet_code = items[3]
            char_sum = sum(ord(x) for x in edinet_code)
            cpu_idx  = char_sum % cpu_count

            public_docs_list[cpu_idx].append( [category_name, public_doc] )

            if not edinet_code in edinet_codes:
                edinet_codes.append(edinet_code)

    return category_edinet_codes, public_docs_list

def f(cpu_count, cpu_id, public_docs_list, progress):
    from xbrl_reader import readXbrlThread

    readXbrlThread(cpu_count, cpu_id, public_docs_list, progress)

if __name__ == '__main__':

    cpu_count = multiprocessing.cpu_count()
    # cpu_count = 1

    progress = Array('i', [0] * cpu_count)
    category_edinet_codes, public_docs_list = make_public_docs_list(cpu_count)

    root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'
    json_path = "%s/data/json/四半期報告書/category_edinet_codes.json" % root_dir
    with codecs.open(json_path, 'w','utf-8') as json_f:
        json.dump(category_edinet_codes, json_f, ensure_ascii=False)

    if cpu_count == 1:
        cpu_id = 0
        f(cpu_count, cpu_id, public_docs_list[cpu_id], progress)

    else:

        process_list = []
        for cpu_id in range(cpu_count):

            p = Process(target=f, args=(cpu_count, cpu_id, public_docs_list[cpu_id], progress))

            process_list.append(p)

            p.start()


        for p in process_list:
            p.join()    

    print('終了:%d' % int(time.time() - start_time) )
