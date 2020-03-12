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
from xbrl_reader import readCalcSub, readCalcArcs, period_names
from download import company_dic
from xbrl_table import all_account_ids

start_time = time.time()

base_annual_context_names = [
    "CurrentYearInstant", "CurrentYearDuration", 
    "Prior1YearInstant", "Prior1YearDuration", 
]

# base_quarterly_context_names = [
#     "CurrentQuarterInstant", "CurrentYTDDuration", "CurrentQuarterDuration",
#     "Prior1QuarterInstant", "Prior1YTDDuration", "Prior1QuarterDuration",
# ]

annual_context_names = base_annual_context_names + [ x + "_NonConsolidatedMember" for x in base_annual_context_names ]
# quarterly_context_names = base_quarterly_context_names + [ x + "_NonConsolidatedMember" for x in base_quarterly_context_names ]
quarterly_context_names = [
    "CurrentQuarterInstant", # 当四半期会計期間連結時点, 
    "CurrentYTDDuration",    # 当四半期累計期間連結期間, 
    "Prior1YearInstant",     # 前期連結時点
    "Prior1YTDDuration",     # 前年度同四半期累計期間連結期間
]

context_names = [ "FilingDateInstant" ] + annual_context_names + quarterly_context_names

    # "Prior1YearInstant_NonConsolidatedMember", "Prior1YearDuration_NonConsolidatedMember", 
    # "Prior1QuarterInstant_NonConsolidatedMember", "Prior1YTDDuration_NonConsolidatedMember", "Prior1QuarterDuration_NonConsolidatedMember",
    # "Prior1YearInstant_NonConsolidatedMember", "Prior1YearDuration_NonConsolidatedMember", 
    # "Prior1QuarterInstant_NonConsolidatedMember", "Prior1YTDDuration_NonConsolidatedMember", "Prior1QuarterDuration_NonConsolidatedMember",
    # "InterimInstant", "InterimInstant_NonConsolidatedMember", "InterimDuration", "InterimDuration_NonConsolidatedMember"  

account_dics = [ {}, {}, {} ]
ns_xsd_dic = {}

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path    = root_dir + '/python/data'
extract_path = root_dir + '/zip/extract'

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

def get_context_type(context_name: str):
    k = context_name.rfind("_NonConsolidatedMember")
    if k != -1:
        context_name = context_name[: k]

    if context_name == "FilingDateInstant":
        # 提出日時点の場合

        return 0
    elif context_name.endswith("Instant"):
        # その他の時点の場合

        return 1
    else:
        assert context_name.endswith("Duration")
        # 期間の場合

        return 2

def collect_values(edinetCode, values, major_context_names, stats, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)        

    if tag_name == "xbrl":
        for child in el:
            collect_values(edinetCode, values, major_context_names, stats, child)
        return

    if text is None:
        return

    context_ref = el.get("contextRef")
    if context_ref is None or not context_ref in context_names:
        return

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

    context_type = get_context_type(context_ref)
    account_dic  = account_dics[context_type]
    if id in account_dic and context_ref in major_context_names:

        major_idx = major_context_names.index(context_ref)

        if ele.type == "stringItemType" and ('\r' in text or '\n' in text):
            text = text.replace('\r', '').replace('\n', '').strip()

        values[major_idx][ account_dic[id] ] = text
        # 報告書インスタンス 作成ガイドライン
        #   5-6-2 数値を表現する要素

    name = '"%s", # %s %s %s' % (id, ele.label, ele.verbose_label, ele.type)

    idx = context_names.index(context_ref)
    stats[idx][name] += 1

def context_display_name(context_ref):
    if context_ref.endswith("_NonConsolidatedMember"):
        name = context_ref.replace("_NonConsolidatedMember", "")
        return period_names[name].replace("連結", "個別")
    else:
        return period_names[context_ref]


def make_titles(context_type):
    account_ids = all_account_ids[context_type]
    account_dic = account_dics[context_type]

    titles = [""] * len(account_ids)
    for i, id in enumerate(account_ids):
        assert not id in account_dic
        account_dic[id] = i

        ns, tag_name = id.split(':')

        assert ns in ns_xsd_dic
        xsd_dic = ns_xsd_dic[ns]
        assert tag_name in xsd_dic
        ele =xsd_dic[tag_name]

        if id in [ "jppfs_cor:DepreciationAndAmortizationOpeCF", "jppfs_cor:DepreciationSGA"]:
            label = ele.verbose_label
        else:
            label = ele.label

        assert not "," in label
        assert not label in titles

        titles[i] = label

    return titles

def get_xbrl_root(cpu_count, cpu_id):
    for zip_path_obj in Path(extract_path).glob("**/E*.zip"):
        zip_path = str(zip_path_obj)

        edinetCode = os.path.basename(zip_path).split('.')[0]
        assert edinetCode[0] == 'E'
        if int(edinetCode[1:]) % cpu_count != cpu_id:
            continue

        try:
            with zipfile.ZipFile(zip_path) as zf:
                for xbrl_file in zf.namelist():
                    with zf.open(xbrl_file) as f:
                        xml_bin = f.read()

                    xml_text = xml_bin.decode('utf-8')
                    root = ET.fromstring(xml_text)

                    yield xbrl_file, root

        except zipfile.BadZipFile:
            print("\nBadZipFile : %s\n" % zip_path)
            continue

def make_summary(cpu_count, cpu_id, ns_xsd_dic_arg):
    global ns_xsd_dic

    for key, dict in ns_xsd_dic_arg.items():
        ns_xsd_dic[key] = dict

    # ns_xsd_dic = ns_xsd_dic_arg
    print("cpu:%d dic:%d" % (cpu_id, len(ns_xsd_dic)))

    csv_f = [None] * 3
    for context_type in range(3):
        csv_f[context_type] = codecs.open("%s/summary-%d-%d.csv" % (data_path, context_type, cpu_id), 'w', 'utf-8')

        titles = make_titles(context_type)
        if context_type == 0:
            csv_f[context_type].write("EDINETコード,会計期間終了日,報告書略号,%s\n" % ",".join(titles) )
        else:
            csv_f[context_type].write("EDINETコード,会計期間終了日,報告書略号,コンテキスト,%s\n" % ",".join(titles) )

    annual_stats = [ Counter() for _ in context_names ]
    quarterly_stats = [ Counter() for _ in context_names ]

    cnt = 0

    for xbrl_file_name, root in get_xbrl_root(cpu_count, cpu_id):

        # 報告書インスタンス作成ガイドライン
            #  4-2-4 XBRLインスタンスファイル XBRLインスタンスファイルの命名規約
                # jp{府令略号}{様式番号}-{報告書略号}-{報告書連番(3桁)}
                # {EDINETコード又はファンドコード}-{追番(3桁)}
                # {報告対象期間期末日|報告義務発生日}
                # {報告書提出回数(2桁)}
                # {報告書提出日}.xbrl

        v1 = xbrl_file_name.split('_')
        if v1[3] != "01":
            # 訂正の場合

            continue

        edinetCode = v1[1].split('-')[0]
        if not edinetCode in company_dic:
            continue

        end_date = v1[2]

        company = company_dic[edinetCode]
        if company['category_name_jp'] in ["保険業", "その他金融業", "証券、商品先物取引業", "銀行業"]:
            continue

        v2 = v1[0].split('-')
        repo = v2[1]
        if repo == "asr":
            stats = annual_stats
            major_context_names = [ "FilingDateInstant" ] + annual_context_names

        elif repo in [ "q1r", "q2r", "q3r", "q4r" ]:
            stats = quarterly_stats
            major_context_names = [ "FilingDateInstant" ] + quarterly_context_names

        elif repo == "ssr":
            continue
        else:
            assert False

        values = [ [""] * len(all_account_ids[ get_context_type(x) ]) for x in major_context_names ]

        collect_values(edinetCode, values, major_context_names, stats, root)
        for idx, context_name in enumerate(major_context_names):
            context_type = get_context_type(context_name)

            if context_type == 0:
                csv_f[context_type].write("%s,%s,%s,%s\n" % (edinetCode, end_date, repo, ",".join(values[idx])) )
            else:
                csv_f[context_type].write("%s,%s,%s,%s,%s\n" % (edinetCode, end_date, repo, context_display_name(context_name), ",".join(values[idx])) )

        cnt += 1
        if cnt % 500 == 0:
            print("cpu:%d cnt:%d" % (cpu_id, cnt))

    for i, stats in enumerate([annual_stats, quarterly_stats]):
        with open("%s/stats-%d-%d.csv" % (data_path, i, cpu_id), 'wb') as f:
            pickle.dump(stats, f)

    for f in csv_f:
        f.close()

    print("合計:%d" % cnt)

def concatenate_stats(cpu_count):
    stats_f = codecs.open("%s/stats.txt" % data_path, 'w', 'utf-8')

    for report_idx, report_name in enumerate([ "有価証券報告書", "四半期報告書" ]):
        stats_f.write("report:\t%s\n" % report_name)
        stats_f.write("\n")

        stats = [ Counter() for _ in context_names ]
        for cpu_id in range(cpu_count):

            stats_path = "%s/stats-%d-%d.csv" % (data_path, report_idx, cpu_id)
            with open(stats_path, 'rb') as f:
                stats_tmp = pickle.load(f)

            os.remove(stats_path)

            for idx, context_name in enumerate(context_names):
                for name, cnt in stats_tmp[idx].items():
                    stats[idx][name] += cnt

        for idx, context_name in enumerate(context_names):
            if len(stats[idx]) == 0:
                continue

            stats_f.write("context:\t%s\n" % context_display_name(context_name) )
            v = list(sorted(stats[idx].items(), key=lambda x:x[1], reverse=True))
            for w, cnt in v[:200]:
                stats_f.write("%s\t%d\n" % (w, cnt))
            stats_f.write("\n")

        stats_f.write("\n")

    stats_f.close()


def concatenate_summary(cpu_count):
    for context_type in range(3):
        summary_all = []
        for cpu_id in range(cpu_count):
            summary_path = "%s/summary-%d-%d.csv" % (data_path, context_type, cpu_id)
            lines = read_lines(summary_path)
            if cpu_id != 0:
                lines = lines[1:]
            summary_all.extend(lines)

            os.remove(summary_path)

        with codecs.open("%s/summary-%d.csv" % (data_path, context_type), 'w', 'utf-8') as f:
            f.write('\n'.join(summary_all))

if __name__ == '__main__':
    with codecs.open(data_path + "/schema.txt", 'w', 'utf-8') as f:
        ReadAllSchema(f)

    cpu_count = multiprocessing.cpu_count()
    process_list = []
    for cpu_id in range(cpu_count):

        p = Process(target=make_summary, args=(cpu_count, cpu_id, ns_xsd_dic))

        process_list.append(p)

        p.start()

    for p in process_list:
        p.join()

    concatenate_summary(cpu_count)

    concatenate_stats(cpu_count)

    print('終了:%d' % int(time.time() - start_time) )
