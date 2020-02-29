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
import pickle
from typing import Dict, List, Any
from collections import OrderedDict
import multiprocessing
from multiprocessing import Process, Array

from xbrl_reader import Inf, SchemaElement, read_lines, ReadSchema, ReadLabel, parseElement, read_company_dic, getAttribs, label_role, verboseLabel_role
from xbrl_reader import readCalcSub, readCalcArcs
from xbrl_get import company_dic, get_xbrl_zip_bin
from xbrl_table import account_ids

start_time = time.time()
context_refs = [ "FilingDateInstant", "CurrentYearInstant", "CurrentYearInstant_NonConsolidatedMember", "CurrentYearDuration", "CurrentYearDuration_NonConsolidatedMember", "CurrentQuarterInstant", "CurrentQuarterInstant_NonConsolidatedMember", "CurrentYTDDuration", "CurrentYTDDuration_NonConsolidatedMember", "InterimInstant", "InterimInstant_NonConsolidatedMember", "InterimDuration", "InterimDuration_NonConsolidatedMember"  ]
account_dic = {}
ns_xsd_dic = {}

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path = root_dir + '/python/data'

def get_xbrl_zip_root(cpu_count, cpu_id):
    for xbrl_file_name, xml_bin in get_xbrl_zip_bin(cpu_count, cpu_id):
        xml_text = xml_bin.decode('utf-8')
        root = ET.fromstring(xml_text)

        yield xbrl_file_name, root

def ReadAllSchema(log_f):
    inf = Inf()

    xsd_label_files = [ 
        [ "jpcrp_cor", "jpcrp/2019-11-01/jpcrp_cor_2019-11-01.xsd", "jpcrp/2019-11-01/label/jpcrp_2019-11-01_lab.xml"],
        [ "jppfs_cor", "jppfs/2019-11-01/jppfs_cor_2019-11-01.xsd", "jppfs/2019-11-01/label/jppfs_2019-11-01_lab.xml"],
        [ "jpdei_cor", "jpdei/2013-08-31/jpdei_cor_2013-08-31.xsd", "jpdei/2013-08-31/label/jpdei_2013-08-31_lab.xml"],
        [ "jpigp_cor", "jpigp/2019-11-01/jpigp_cor_2019-11-01.xsd", "jpigp/2019-11-01/label/jpigp_2019-11-01_lab.xml"]
    ]

    for prefix, xsd_file, lable_file in xsd_label_files:
        xsd_path = "%s/data/EDINET/taxonomy/2019-11-01/taxonomy/%s" % (root_dir, xsd_file)

        xsd_dic : Dict[str, SchemaElement] = {}

        xsd_tree = ET.parse(xsd_path)
        xsd_root = xsd_tree.getroot()

        # スキーマファイルの内容を読む。
        ReadSchema(inf, False, xsd_path, xsd_root, xsd_dic)

        label_path = "%s/data/EDINET/taxonomy/2019-11-01/taxonomy/%s" % (root_dir, lable_file)
        label_tree = ET.parse(label_path)
        label_root = label_tree.getroot()

        resource_dic = {}
        loc_dic = {}
        # 名称リンクファイルの内容を読む。
        ReadLabel(label_root, xsd_dic, loc_dic, resource_dic)

        if prefix == "jppfs_cor":

            xsd_base = os.path.dirname(xsd_path)

            # フォルダーの下の計算リンクファイルに対し
            for xml_path_obj in Path(xsd_base).glob('r/*/*_cal_*.xml'):
                xml_path = str(xml_path_obj).replace('\\', '/')
                locs = {}
                arcs = []

                # 計算リンクファイルの内容を読む。
                readCalcSub(inf, ET.parse(xml_path).getroot(), xsd_dic, locs, arcs)

                # 計算リンクの計算関係を得る。
                readCalcArcs(xsd_dic, locs, arcs)

            print("計算リンク 終了")
            for ele in OrderedDict.fromkeys(xsd_dic.values()).keys():
                if len(ele.calcTo) != 0:
                    log_f.write(ele.verbose_label + '\n')
                    for calc in ele.calcTo:
                        log_f.write("\t%s %f %s %s\n" % (calc.to.verbose_label, calc.order, calc.weight, calc.role))

        ns_xsd_dic[prefix] = xsd_dic

    # assert xsd_dics[uri] == xsd_dic

def xbrl_test(edinetCode, values, vloc, vcnt, vifrs, vusgaap, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)        

    if tag_name == "xbrl":
        for child in el:
            xbrl_test(edinetCode, values, vloc, vcnt, vifrs, vusgaap, child)
        return

    if text is None:
        return

    context_ref = el.get("contextRef")
    if context_ref is None or not context_ref in context_refs: # context_ref.startswith("Prior"):
        return

    idx = context_refs.index(context_ref)

    ns = uri.split('/')[-1]

    ele = None
    if ns in ns_xsd_dic:
        xsd_dic = ns_xsd_dic[ns]
        if tag_name in xsd_dic:
            ele =xsd_dic[tag_name]
            if ele.type in ["textBlockItemType"]:
                return

    if ele is None:
        return

    id = "%s:%s" % (ns, tag_name)
    if id in account_dic:
        if ele.type == "stringItemType" and ('\r' in text or '\n' in text):
            text = text.replace('\r', '').replace('\n', '').strip()

        values[account_dic[id]] = text
        # 報告書インスタンス 作成ガイドライン
        #   5-6-2 数値を表現する要素

    name = '"%s:%s", # %s %s %s' % (ns, tag_name, ele.label, ele.verbose_label, ele.type)
    # name = context_ref

    vloc[idx][name] += 1

    if "IFRS" in tag_name:
        vifrs[idx][name] += 1
    elif "USGAAP" in tag_name:
        vusgaap[idx][name] += 1
    else:
        vcnt[idx][name] += 1

def make_titles():
    titles = []
    for i, id in enumerate(account_ids):
        assert not id in account_dic
        account_dic[id] = i

        ns, tag_name = id.split(':')

        assert ns in ns_xsd_dic
        xsd_dic = ns_xsd_dic[ns]
        assert tag_name in xsd_dic
        ele =xsd_dic[tag_name]

        assert not "," in ele.label
        assert not ele.label in titles
        titles.append(ele.label)

    return titles

def print_context_freq(log_f, vcnt):
    for idx, context_ref in enumerate(context_refs):
        if len(vcnt[idx]) == 0:
            continue

        log_f.write("context:\t%s\n" % context_ref)
        v = list(sorted(vcnt[idx].items(), key=lambda x:x[1], reverse=True))
        for w, cnt in v[:200]:
            log_f.write("%s\t%d\n" % (w, cnt))
        log_f.write("\n")

    log_f.write("\n")

def make_csv(cpu_count, cpu_id, ns_xsd_dic_arg):
    global ns_xsd_dic

    for key, dict in ns_xsd_dic_arg.items():
        ns_xsd_dic[key] = dict

    # ns_xsd_dic = ns_xsd_dic_arg
    print("cpu:%d dic:%d" % (cpu_id, len(ns_xsd_dic)))

    csv_f = codecs.open("%s/report-%d.csv" % (data_path, cpu_id), 'w', 'utf-8')

    titles = make_titles()
    csv_f.write("%s\n" % ",".join(titles) )

    vcnt1 = [ Counter() for _ in context_refs ]
    vcnt2 = [ Counter() for _ in context_refs ]
    vcnt3 = [ Counter() for _ in context_refs ]
    vifrs = [ Counter() for _ in context_refs ]
    vusgaap = [ Counter() for _ in context_refs ]

    cnt = 0
    for xbrl_file_name, root in get_xbrl_zip_root(cpu_count, cpu_id):
        v1 = xbrl_file_name.split('_')
        if v1[3] != "01":
            # 訂正の場合

            continue

        edinetCode = v1[1].split('-')[0]
        if not edinetCode in company_dic:
            continue

        # if int(edinetCode[1:]) % cpu_count != cpu_id:
        #     continue

        company = company_dic[edinetCode]
        if company['category_name_jp'] in ["保険業", "その他金融業", "証券、商品先物取引業", "銀行業"]:
            continue

        v2 = v1[0].split('-')
        repo = v2[1]
        if repo == "asr":
            vcnt = vcnt1
        elif repo in [ "q1r", "q2r", "q3r", "q4r" ]:
            vcnt = vcnt2
        elif repo == "ssr":
            vcnt = vcnt3
        else:
            assert False

        vloc  = [ Counter() for _ in context_refs ]
        values = [""] * len(account_ids)
        xbrl_test(edinetCode, values, vloc, vcnt, vifrs, vusgaap, root)
        csv_f.write("%s\n" % ",".join(values) )

        if sum(len(x) for x in vloc) == 0:
            print(xbrl_file_name, company['category_name_jp'])

        cnt += 1
        if cnt % 1000 == 0:
            print("cpu:%d cnt:%d" % (cpu_id, cnt))
            with codecs.open("%s/log-%d.txt" %(data_path, cpu_id), 'w', 'utf-8') as log_f:
                for txt, v in [ ["有価証券報告書", vcnt1], ["四半期報告書", vcnt2], ["中間期報告書", vcnt3], ["IFRS", vifrs], ["USGAAP", vusgaap] ]:
                    log_f.write("report:\t%s\n" % txt)
                    print_context_freq(log_f, v)
                    log_f.write("\n")

    csv_f.close()
    print("合計:%d" % cnt)

def concatenate_report(cpu_count):
    report_all = []
    for cpu_id in range(cpu_count):
        report_path = "%s/report-%d.csv" % (data_path, cpu_id)
        lines = read_lines(report_path)
        if cpu_id != 0:
            lines = lines[1:]
        report_all.extend(lines)

        os.remove(report_path)

    with codecs.open("%s/report.csv" % data_path, 'w', 'utf-8') as f:
        f.writelines(report_all)

if __name__ == '__main__':
    with codecs.open(data_path + "/schema.txt", 'w', 'utf-8') as f:
        ReadAllSchema(f)

    cpu_count = multiprocessing.cpu_count()
    cpu_count = 1
    process_list = []
    for cpu_id in range(cpu_count):

        p = Process(target=make_csv, args=(cpu_count, cpu_id, ns_xsd_dic))

        process_list.append(p)

        p.start()

    for p in process_list:
        p.join()

    concatenate_report(cpu_count)

    print('終了:%d' % int(time.time() - start_time) )

    # make_csv()
