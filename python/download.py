import datetime
import os
import sys
import json
from collections import Counter
from pathlib import Path
import urllib.request
import codecs
import zipfile
import xml.etree.ElementTree as ET
import time
import re
import random
from typing import Dict, List, Any
from collections import OrderedDict

from xbrl_reader import Inf, SchemaElement, Calc, init_xbrl_reader, read_company_dic, readXbrlThread, make_public_docs_list, read_lines, parseElement, getAttribs, label_role, verboseLabel_role, find
from xbrl_reader import readCalcSub, readCalcArcs, xsd_dics

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
report_path = root_dir + '/web/report'

data_path = root_dir + '/python/data'
docs_path = root_dir + '/xbrl-zip'
group_path = root_dir + '/group-zip'

for path in [data_path, docs_path]:
    if not os.path.exists(path):
        # フォルダーがなければ作る。

        os.makedirs(path)

company_dic = read_company_dic()

def print_freq(vcnt, top):
    v = list(sorted(vcnt.items(), key=lambda x:x[1], reverse=True))
    for w, cnt in v[:top]:
        print(w, cnt)

def receive_edinet_doc_list(day_path: str, url: str):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = json.load(res)

    assert body['metadata']['message'] == "OK"

    # JSONをファイルに書く。
    json_path = "%s/docs.json" % day_path
    with codecs.open(json_path, 'w', 'utf-8') as json_f:
        json.dump(body, json_f, ensure_ascii=False)

    return body

def check_zip_file(zip_path: str):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            file_list = list(zf.namelist())

        return True
    except zipfile.BadZipFile:
        return False

def receive_edinet_doc(yyyymmdd, doc, edinetCode, company, dst_path):
    assert edinetCode == doc['edinetCode']
    assert company == company_dic[edinetCode]

    print("%s | %s | %s | %s | %s" % (yyyymmdd, doc['filerName'], doc['docDescription'], company['listing'], company['category_name']))

    url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/%s?type=1" % doc['docID']
    with urllib.request.urlopen(url) as web_file:
        data = web_file.read()

        with open(dst_path, mode='wb') as local_file:
            local_file.write(data)

        if not check_zip_file(dst_path):
            print("!!!!!!!!!! ERROR !!!!!!!!!!\n" * 1)
            print("msg:[%s] status:[%s] reason:[%s]" % (str(web_file.msg), str(web_file.status), str(web_file.reason) ))
            print("!!!!!!!!!! ERROR [%s] !!!!!!!!!!\n" % dst_path)
            print(json.dumps(doc, indent=2, ensure_ascii=False))
            print("!!!!!!!!!! ERROR !!!!!!!!!!\n" * 1)
            time.sleep(10)

    time.sleep(1)

def select_doc(day_path, body):
    for doc in body['results']:   
        docTypeCode = doc['docTypeCode']
        if docTypeCode in [ '120', '130', '140', '150', '160', '170' ] and doc['docInfoEditStatus'] == "0":
            edinetCode = doc['edinetCode']
            if edinetCode in company_dic:
                company = company_dic[edinetCode]
                if company['listing'] == '上場':

                    dst_path = "%s/%s-%s-%d.zip" % (day_path, edinetCode, docTypeCode, doc['seqNumber'])

                    yield [ doc, edinetCode, company, dst_path ]

def get_xbrl_docs():
    # dt1 = datetime.datetime(year=2018, month=8, day=10)
    dt1 = datetime.datetime.today()
    
    while True:
        dt1 = dt1 + datetime.timedelta(days=-1)
            
        yyyymmdd = "%d-%02d-%02d" % (dt1.year, dt1.month, dt1.day)
        print(yyyymmdd)

        day_path = "%s/%d/%02d/%02d" % (docs_path, dt1.year, dt1.month, dt1.day)
        if not os.path.exists(day_path):
            # フォルダーがなければ作る。

            os.makedirs(day_path)

        os.chdir(day_path)

        json_path = "%s/docs.json" % day_path
        if os.path.exists(json_path):
            with codecs.open(json_path, 'r', 'utf-8') as f:
                body = json.load(f)

        else:
            url = 'https://disclosure.edinet-fsa.go.jp/api/v1/documents.json?date=%s&type=2' % yyyymmdd
            body = receive_edinet_doc_list(day_path, url)
            time.sleep(1)

        for doc, edinetCode, company, dst_path in select_doc(day_path, body):
            if os.path.exists(dst_path) and check_zip_file(dst_path):
                continue

            receive_edinet_doc(yyyymmdd, doc, edinetCode, company, dst_path)

def group_zip():
    dic = {}
    for zip_path_obj in Path(docs_path).glob("**/*.zip"):
        zip_path = str(zip_path_obj)
        edinetCode = os.path.basename(zip_path).split('-')[0]
        if edinetCode in dic:
            dic[edinetCode].append(zip_path)
        else:
            dic[edinetCode] = [ zip_path ]

    if not os.path.exists(group_path):
        # フォルダーがなければ作る。

        os.makedirs(group_path)

    xbrl = re.compile('XBRL/PublicDoc/jpcrp[-_0-9a-zA-Z]+\.xbrl')

    log_f = codecs.open("%s/group_log.txt" % data_path, 'w', 'utf-8')

    for edinetCode, zip_paths in dic.items():
        group_zip_path = "%s/%s.zip" % (group_path, edinetCode)
        print(group_zip_path)
        with zipfile.ZipFile(group_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
            for zip_path in zip_paths:
                try:
                    with zipfile.ZipFile(zip_path) as zf:
                        xbrl_file = find(x for x in zf.namelist() if xbrl.match(x))
                        if xbrl_file is None:
                            # print("no xbrl", zip_path)
                            continue

                        with zf.open(xbrl_file) as f:
                            xml_bin = f.read()

                        file_name = xbrl_file.split('/')[-1]
                        new_zip.writestr(file_name, xml_bin)

                except zipfile.BadZipFile:
                    print("\nBadZipFile : %s\n" % zip_path)
                    log_f.write("BadZipFile:[%s]\n" % zip_path)
                    continue

    log_f.close()

if __name__ == '__main__':

    args = sys.argv
    if len(args) == 2:
        if args[1] == "get":
            get_xbrl_docs()

        elif args[1] == "group":
            group_zip()

