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

company_dic = read_company_dic()

def print_freq(vcnt, top):
    v = list(sorted(vcnt.items(), key=lambda x:x[1], reverse=True))
    for w, cnt in v[:top]:
        print(w, cnt)

def getDocList(day_path: str, url: str):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = json.load(res)

    assert body['metadata']['message'] == "OK"

    # JSONをファイルに書く。
    json_path = "%s/docs.json" % day_path
    with codecs.open(json_path, 'w', 'utf-8') as json_f:
        json.dump(body, json_f, ensure_ascii=False)

    return body

def download_file(url, dst_path):
    with urllib.request.urlopen(url) as web_file:
        data = web_file.read()
        with open(dst_path, mode='wb') as local_file:
            local_file.write(data)

    # try:
    # except urllib.error.URLError as e:
    #     print(e)

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
report_path = root_dir + '/web/report'

data_path = root_dir + '/python/data'
docs_path = root_dir + '/xbrl-zip'

for path in [data_path, docs_path]:
    if not os.path.exists(path):
        # フォルダーがなければ作る。

        os.makedirs(path)

class Account:
    label: str
    verboseLabel: str
    elementName: str
    type: str
    depth: int

    def __init__(self, items):
        self.label = items[1]
        self.verboseLabel = items[2]
        self.elementName = items[8]
        self.type = items[9]
        self.depth = int(items[14])


def read_jpcrp_labelArc(el: ET.Element, labelArcs):
    id, uri, tag_name, text = parseElement(el)

    if tag_name == "labelArc":
        attr = getAttribs(el)

        assert 'from' in attr and 'to' in attr
        labelArcs[attr['to']] = attr['from']

    for child in el:
        read_jpcrp_labelArc(child, labelArcs)


def read_jpcrp_label(el: ET.Element, labelArcs, label_dic, verbose_label_dic):
    id, uri, tag_name, text = parseElement(el)


    if tag_name == "label":

        attr = getAttribs(el)
        assert 'label' in attr and 'role' in attr
        assert attr['label'] in labelArcs
        label = labelArcs[attr['label']]

        if attr['role'] == label_role:
            label_dic[label] = el.text
        elif attr['role'] == verboseLabel_role:
            verbose_label_dic[label] = el.text

    # 再帰的にXBRLファイルの内容を読む。
    for child in el:
        read_jpcrp_label(child, labelArcs, label_dic, verbose_label_dic)


def read_label():
    label_path = "%s/data/EDINET/taxonomy/2019-11-01/taxonomy/jpcrp/2019-11-01/label/jpcrp_2019-11-01_lab.xml" % root_dir
    root = ET.parse(label_path).getroot()
    labelArcs = {}
    read_jpcrp_labelArc(root, labelArcs)

    label_dic = {}
    verbose_label_dic = {}
    read_jpcrp_label(root, labelArcs, label_dic, verbose_label_dic)

    return label_dic, verbose_label_dic

def readAccounts():
    path = '%s/data/EDINET/勘定科目リスト.csv' % root_dir
    lines = read_lines(path)
    
    accounts = {}

    lines = lines[2:]
    for line in lines:
        items = line.split('\t')

        # 0:科目分類 1:標準ラベル（日本語） 2:冗長ラベル（日本語） 3:標準ラベル（英語） 4:冗長ラベル（英語） 5:用途区分、財務諸表区分及び業種区分のラベル（日本語） 6:用途区分、財務諸表区分及び業種区分のラベル（英語） 7:名前空間プレフィックス 8:要素名 9:type 10:substitutionGroup 11:periodType 12:balance 13:abstract 14:depth
        if len(items) != 15 or items[7] != 'jppfs_cor':
            continue

        account = Account(items)
        accounts[account.elementName] = account

    return accounts

def get_xbrl_zip_bin(cpu_count, cpu_id):
    xbrl = re.compile('XBRL/PublicDoc/jpcrp[-_0-9a-zA-Z]+\.xbrl')

    for _, _, zip_path in get_zip_path():

        edinetCode = os.path.basename(zip_path).split('-')[0]
        assert edinetCode[0] == 'E'
        if int(edinetCode[1:]) % cpu_count != cpu_id:
            continue

        if not os.path.exists(zip_path):
            print("no file:%s" % zip_path)
            continue

        try:
            with zipfile.ZipFile(zip_path) as zf:
                xbrl_file = find(x for x in zf.namelist() if xbrl.match(x))
                if xbrl_file is None:
                    # print("no xbrl", zip_path)
                    continue

                with zf.open(xbrl_file) as f:
                    xml_bin = f.read()
        except zipfile.BadZipFile:
            print("\nBadZipFile : %s\n" % zip_path)
            continue
                
        xbrl_file_name = xbrl_file.split('/')[-1]
        yield xbrl_file_name, xml_bin

def get_xbrl_root():
    dir_path = "%s/xbrl-xml" % root_dir
    for xml_path_obj in Path(dir_path).glob("**/*.xbrl"):
        xml_path = str(xml_path_obj)
        xbrl_file_name = xml_path.split(os.sep)[-1]
        root = ET.parse(xml_path).getroot()

        yield xbrl_file_name, root

def check_zip_file(zip_path: str):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            file_list = list(zf.namelist())

        return True
    except zipfile.BadZipFile:
        return False

def download_check_zip_file(yyyymmdd, doc, dst_path):
    if os.path.exists(dst_path) and check_zip_file(dst_path):
        return

    edinetCode = doc['edinetCode']
    company = company_dic[edinetCode]

    print("%s | %s | %s | %s | %s" % (yyyymmdd, doc['filerName'], doc['docDescription'], company['listing'], company['category_name']))

    url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/%s?type=1" % doc['docID']
    download_file(url, dst_path)

    if not check_zip_file(dst_path):
        print("!!!!!!!!!! ERROR !!!!!!!!!!\n" * 10)
        time.sleep(10)

    time.sleep(1)

def download_docs(yyyymmdd, day_path, body):
    for doc in body['results']:   
        docTypeCode = doc['docTypeCode']
        if docTypeCode in [ '120', '130', '140', '150', '160', '170' ] and doc['docInfoEditStatus'] == "0":
            edinetCode = doc['edinetCode']
            if edinetCode in company_dic:
                company = company_dic[edinetCode]
                if company['listing'] == '上場':

                    dst_path = "%s/%s-%s-%d.zip" % (day_path, edinetCode, docTypeCode, doc['seqNumber'])

                    yield [ doc, docTypeCode, edinetCode, company, dst_path ]

def get_xbrl_docs():
    dt1 = None
    
    while True:
        if dt1 is None:
            dt1 = datetime.datetime(year=2018, month=8, day=10)
        else:
            dt1 = dt1 + datetime.timedelta(days=-1)
            
        yyyymmdd = "%d-%02d-%02d" % (dt1.year, dt1.month, dt1.day)
        print(yyyymmdd)

        day_path = "%s/%d/%02d/%02d" % (docs_path, dt1.year, dt1.month, dt1.day)
        if not os.path.exists(day_path):
            # フォルダーがなければ作る。

            os.makedirs(day_path)

        os.chdir(day_path)

        url = 'https://disclosure.edinet-fsa.go.jp/api/v1/documents.json?date=%s&type=2' % yyyymmdd
        body = getDocList(day_path, url)
        time.sleep(1)

        for doc, dst_path in download_docs(yyyymmdd, day_path, body):
            download_check_zip_file(yyyymmdd, doc, dst_path)

def get_zip_path():
    for json_path_obj in Path(docs_path).glob("**/docs.json"):
        json_path = str(json_path_obj)

        paths = json_path.split(os.sep)
        yyyymmdd = "%s-%s-%s" % (paths[-4], paths[-3], paths[-2])
        day_path = "%s/%s/%s/%s" % (docs_path, paths[-4], paths[-3], paths[-2])

        with codecs.open(json_path, 'r', 'utf-8') as f:
            body = json.load(f)

        for doc, docTypeCode, edinetCode, company, dst_path in download_docs(yyyymmdd, day_path, body):
            yield [yyyymmdd, doc, dst_path]

def retry_get_xbrl_docs():
    for yyyymmdd, doc, dst_path in get_zip_path():
        download_check_zip_file(yyyymmdd, doc, dst_path)



def extract_xbrl():
    cnt = 0
    for xbrl_file, xml_bin in get_xbrl_zip_bin(cpu_count, cpu_id):
        v1 = xbrl_file.split('_')
        v2 = v1[1].split('-')
        edinetCode = v2[0]
        if edinetCode in company_dic:
            category_name = company_dic[edinetCode]["category_name"]
        else:
            category_name = "other"

        dir_path = "%s/xbrl-xml/%s/%s" % (root_dir, category_name, edinetCode)
        if not os.path.exists(dir_path):
            # フォルダーがなければ作る。

            os.makedirs(dir_path)

        xml_path = dir_path + "/" + xbrl_file
        with open(xml_path, "wb") as f:
            f.write(xml_bin)

        cnt += 1
        if cnt % 100 == 0:
            print(cnt)

    print("合計 : %d" % cnt)

def xbrl_test_ifrs(vcnt, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)
    if "IFRS" in tag_name:

        context_ref = el.get("contextRef")

        if context_ref is not None and not context_ref.startswith("Prior"):

            uri.split('/')[-1]
            if tag_name in verbose_label_dic:
                jp = ":" + verbose_label_dic[tag_name]
            else:
                jp = ""
            vcnt[uri.split('/')[-1] + ":" + tag_name + jp] += 1
            return

    for child in el:
        xbrl_test_ifrs(vcnt, child)


if __name__ == '__main__':

    args = sys.argv
    if len(args) == 2:
        if args[1] == "get":
            get_xbrl_docs()

        elif args[1] == "retry":
            retry_get_xbrl_docs()

        elif args[1] == "extract":
            extract_xbrl()
