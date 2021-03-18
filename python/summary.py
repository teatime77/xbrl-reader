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
from enum import IntEnum

from xbrl_reader import Inf, SchemaElement, read_lines, ReadSchema, ReadLabel, parseElement, read_company_dic, getAttribs, label_role, verboseLabel_role
from xbrl_reader import readCalcSub, readCalcArcs, period_names
from download import company_dic
from xbrl_table import all_account_ids, filing_date_account_ids
from stats import write_calc_tree

start_time = time.time()

class ContextType(IntEnum):
    FilingDate = 0  # 提出日時点
    Instant = 1     # 会計終了時点
    Duration = 2    # 会計期間

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

fixed_ids = False
account_dics = [ {}, {}, {} ]
ns_xsd_dic = {}
verbose_label_dic = {}

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path    = root_dir + '/python/data'
extract_path = root_dir + '/zip/extract'

def ReadAllSchema():
    """スキーマと名称リンクと計算リンクのファイルを読む。
    """
    inf = Inf()

    xsd_label_files = [ 
        [ "jpcrp_cor", "jpcrp/2019-11-01/jpcrp_cor_2019-11-01.xsd", "jpcrp/2019-11-01/label/jpcrp_2019-11-01_lab.xml"],
        [ "jppfs_cor", "jppfs/2019-11-01/jppfs_cor_2019-11-01.xsd", "jppfs/2019-11-01/label/jppfs_2019-11-01_lab.xml"],
        [ "jpdei_cor", "jpdei/2013-08-31/jpdei_cor_2013-08-31.xsd", "jpdei/2013-08-31/label/jpdei_2013-08-31_lab.xml"],
        [ "jpigp_cor", "jpigp/2019-11-01/jpigp_cor_2019-11-01.xsd", "jpigp/2019-11-01/label/jpigp_2019-11-01_lab.xml"]
    ]

    for prefix, xsd_file, lable_file in xsd_label_files:
        print('EDINETタクソノミの読み込み中・・・ : %s' % prefix)

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

        if prefix in [ "jppfs_cor", "jpigp_cor" ]:
            xsd_base = os.path.dirname(xsd_path)

            # フォルダーの下の計算リンクファイルに対し
            for xml_path_obj in Path(xsd_base).glob('r/**/*_cal_*.xml'):
                xml_path = str(xml_path_obj).replace('\\', '/')
                locs = {}
                arcs = []

                # 計算リンクファイルの内容を読む。
                readCalcSub(inf, ET.parse(xml_path).getroot(), xsd_dic, locs, arcs)

                # 計算リンクの計算関係を得る。
                readCalcArcs(xsd_dic, locs, arcs)

        ns_xsd_dic[prefix] = xsd_dic

        for ele in xsd_dic.values():
            if ele.verbose_label in verbose_label_dic:
                # 冗長ラベルの辞書にある場合

                # 辞書にあるものと同じはず
                assert verbose_label_dic[ele.verbose_label] == ele
            else:
                # 冗長ラベルの辞書にない場合

                # 辞書に追加する。
                verbose_label_dic[ele.verbose_label] = ele

    # assert xsd_dics[uri] == xsd_dic

def get_context_type(context_name: str):
    """コンテストのタイプを返す。

    * 0: 提出日時点
    * 1: 会計末時点
    * 2: 会計期間

    Args:
        context_name(str) : コンテスト名

    Returns:
        int : コンテストのタイプ
    """
    k = context_name.rfind("_NonConsolidatedMember")
    if k != -1:
        context_name = context_name[: k]

    if context_name == "FilingDateInstant":
        # 提出日時点の場合

        return ContextType.FilingDate
    elif context_name.endswith("Instant"):
        # 会計末時点の場合

        return ContextType.Instant
    else:
        assert context_name.endswith("Duration")
        # 会計期間の場合

        return ContextType.Duration

def collect_values(edinetCode: str, values, major_context_names, stats, el: ET.Element):
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

    # 名前空間を得る。
    ns = uri.split('/')[-1]

    ele = None
    if ns in ns_xsd_dic:
        # 名前空間に対応するスキーマの辞書がある場合

        xsd_dic = ns_xsd_dic[ns]
        if tag_name in xsd_dic:
            # タグ名に対応する要素がスキーマの辞書にある場合

            # タグ名に対応する要素を得る。
            ele =xsd_dic[tag_name]
            if ele.type in ["textBlockItemType"]:
                # テキストブロックの場合

                return

    if ele is None:
        return

    id = "%s:%s" % (ns, tag_name)

    # コンテストのタイプを得る。
    context_type = get_context_type(context_ref)

    # コンテストのタイプに対応する項目の辞書を得る。
    account_dic  = account_dics[context_type]

    if context_ref in major_context_names:
        # 集計対象のコンテストの場合

        if fixed_ids:
            # 項目が固定の場合

            if not id in account_dic and '（IFRS）' in ele.verbose_label:
                # 集計対象のIDでなく、冗長ラベルに'（IFRS）'が含まれる場合

                # 冗長ラベルから'（IFRS）'を取り除く。
                verbose_label = ele.verbose_label.replace('（IFRS）', '')
                
                if verbose_label in verbose_label_dic:
                    # 冗長ラベルの辞書にある場合

                    # 'Japan GAAP'の要素で代用する。
                    ele = verbose_label_dic[verbose_label]
                    id  = ele.id.replace('_cor_', '_cor:')

        if id in account_dic:
            # 集計対象のIDの場合

            major_idx = major_context_names.index(context_ref)

            if ele.type == "stringItemType":
                # 文字列の場合
                
                # エスケープ処理をする。
                text = json.dumps(text, ensure_ascii=False)

            values[major_idx][ account_dic[id] ] = text

    if context_type != ContextType.FilingDate and ele.type in [ "stringItemType", "dateItemType", "booleanItemType" ]:
        # 提出日時点以外のコンテストで、型が数値でない場合

        return

    idx = context_names.index(context_ref)
    stats[idx][id] += 1

def context_display_name(context_ref: str):
    """コンテストの日本語名を返す。

    Args:
        context_ref(str): コンテスト名

    Returns:
        str : コンテストの日本語名
    """
    if context_ref.endswith("_NonConsolidatedMember"):
        # 個別決算の場合

        name = context_ref.replace("_NonConsolidatedMember", "")
        return period_names[name].replace("連結", "個別")
    else:
        # 連結決算の場合

        return period_names[context_ref]


def make_titles(context_type: str) -> List[str]:
    """CSVファイルの先頭行に表示する項目名のリストを返す。

    Args:
        context_type(str)   : コンテスト名

    Returns:
        List[str]: 項目名のリスト
    """
    account_ids = all_account_ids[context_type]
    account_dic = account_dics[context_type]
    assert len(account_ids) == len(set(account_ids))

    # 項目名のリスト
    titles = [""] * len(account_ids)

    # スキーマの要素のリスト
    eles   = [None] * len(account_ids)

    for id_idx, id in enumerate(account_ids):
        assert not id in account_dic
        account_dic[id] = id_idx

        # 名前空間とタグ名を得る。
        ns, tag_name = id.split(':')

        # 名前空間に対応するスキーマの辞書を得る。
        assert ns in ns_xsd_dic
        xsd_dic = ns_xsd_dic[ns]

        # タグ名に対応する要素を得る。
        assert tag_name in xsd_dic
        ele =xsd_dic[tag_name]

        if ele.label in titles:
            # すでに同じラベルがある場合

            # 重複するラベルの位置
            i = titles.index(ele.label)

            # 冗長ラベルが重複しないはず。
            assert ele.verbose_label != eles[i].verbose_label

            # 冗長ラベルを使う。
            titles[i] = eles[i].verbose_label
            label = ele.verbose_label
        else:
            # 同じラベルがない場合

            label = ele.label

        assert not label in titles
        assert not "," in label

        eles[id_idx]   = ele
        titles[id_idx] = label

    return titles

def get_xbrl_root(cpu_count, cpu_id):
    """CPUごとのサブプロセスの処理

    EDINETコードをCPU数で割った余りがCPU-IDに等しければ処理をする。

    Args:
        cpu_count(int): CPU数
        cpu_id   (int): CPU-ID (0, ..., CPU数 - 1)

    Returns:
        XBRLファイルの名前とパースしたルート
    """
    for zip_path_obj in Path(extract_path).glob("**/E*.zip"):
        zip_path = str(zip_path_obj)

        edinetCode = os.path.basename(zip_path).split('.')[0]
        assert edinetCode[0] == 'E'
        if int(edinetCode[1:]) % cpu_count != cpu_id:
            continue

        try:
            # 抽出先のZIPファイルを読み込みモードで開く。
            with zipfile.ZipFile(zip_path) as zf:

                # 期末日とファイル名のペアのリスト
                enddate_filename = [ [x.split('_')[2], x] for x in zf.namelist()  ]

                # 期末日の順にソートする。
                enddate_filename = sorted(enddate_filename, key=lambda x: x[0])

                # ZIPファイル内のXBRLファイルに対し
                for _, xbrl_file in enddate_filename:

                    # XBRLファイルのデータを読む。
                    with zf.open(xbrl_file) as f:
                        xml_bin = f.read()

                    # バイナリデータをutf-8テキストとしてデコードする。
                    xml_text = xml_bin.decode('utf-8')

                    # XBRLファイルのテキストをパースする。
                    root = ET.fromstring(xml_text)

                    yield xbrl_file, root

        except zipfile.BadZipFile:
            print("\nBadZipFile : %s\n" % zip_path)
            continue

def read_stats_json():
    """出現頻度ののJSONファイルを読む。
    """
    global all_account_ids, filing_date_account_ids

    # 出現頻度のJSONファイルを読む。
    # 前回の実行で作ったstats.jsonをstats-master.jsonにリネームしておく。
    stats_master_path = '%s/stats-master.json' % data_path
    if not os.path.exists(stats_master_path):
        # stats-master.jsonがない場合

        stats_path = '%s/stats.json' % data_path
        if os.path.exists(stats_path):
            # stats.jsonがある場合

            print('\n    %sを、stats-master.jsonにリネームしてから実行してください。' % stats_path)

        else:
            # stats.jsonがない場合

            print('\n    %sがありません。\n' % stats_master_path)
            print('    以下の手順を実行してください。\n')
            print('    1. 引数にfixをつけて実行します。\n')
            print('        python summary.py fix\n')
            print('    2. %sを、stats-master.jsonにリネームします。' % stats_path)

        sys.exit()

    with codecs.open(stats_master_path, 'r', 'utf-8') as f:
        stats_json = json.load(f)

    # コンテストのタイプごとに使用する項目のsetのリスト
    all_account_ids = [ set(), set(), set() ]

    # 報告書の種類ごとに
    for report_name, report_json in stats_json.items():

        # 会計基準ごとに
        for accounting_standard, accounting_json in report_json.items():

            # コンテキストごとに
            for context_name, context_json in accounting_json.items():
                if context_name.startswith('Prior'):
                    # 前期、前々期などの場合

                    continue

                # コンテストのタイプごとに使用する項目のset
                ids = all_account_ids[get_context_type(context_name)]
                valid_cnt = 0

                # 項目ごとに
                for id, v in context_json.items():
                    if v[3] in [ "stringItemType", "dateItemType" ]:
                        # 文字列か日付の場合

                        if id != "jpdei_cor:AccountingStandardsDEI":
                            # 会計基準でない場合

                            continue

                    # booleanItemType, nonNegativeIntegerItemType, monetaryItemType, perShareItemType, percentItemType, decimalItemType, sharesItemType

                    # 使用する項目のsetに追加する。
                    ids.add(id)

                    valid_cnt += 1
                    if valid_cnt == 200:
                        # 出現頻度の上位200個の項目のみ使う。

                        break

    # setをlistに変換する。
    all_account_ids = [list(x) for x in all_account_ids]

    # 提出日時点
    filing_date_account_ids = all_account_ids[0]

def make_summary(fixed_ids_arg, cpu_count, cpu_id, ns_xsd_dic_arg, verbose_label_dic_arg, all_account_ids_arg, filing_date_account_ids_arg):
    """CPUごとのサブプロセスの処理

    EDINETコードをCPU数で割った余りがCPU-IDに等しければ処理をする。

    Args:
        cpu_count(int) : CPU数
        cpu_id   (int) : CPU-ID (0, ..., CPU数 - 1)
        ns_xsd_dic_arg : スキーマの辞書
    """

    global fixed_ids, ns_xsd_dic, verbose_label_dic, all_account_ids, filing_date_account_ids

    fixed_ids = fixed_ids_arg
    for key, dict in ns_xsd_dic_arg.items():
        ns_xsd_dic[key] = dict

    verbose_label_dic = verbose_label_dic_arg.copy()
    all_account_ids         = all_account_ids_arg
    filing_date_account_ids = filing_date_account_ids_arg

    # ns_xsd_dic = ns_xsd_dic_arg
    print("start subprocess cpu-id:%d" % cpu_id)

    csv_f = [None, None, None]
    for context_type in range(3):
        csv_f[context_type] = codecs.open("%s/summary-%d-%d.csv" % (data_path, context_type, cpu_id), 'w', 'utf-8')

        # CSVファイルの先頭行に表示する項目名のリスト
        titles = make_titles(context_type)
        if context_type == 0:
            # 提出日時点の場合

            csv_f[context_type].write("EDINETコード,会計期間終了日,報告書略号,%s\n" % ",".join(titles) )
        else:
            # 会計末時点か会計期間の場合

            csv_f[context_type].write("EDINETコード,会計期間終了日,報告書略号,コンテキスト,%s\n" % ",".join(titles) )

    annual_account_stats = {}
    quarterly_account_stats = {}

    cnt = 0

    # XBRLファイルの名前とパースしたルートに対し
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
            # 銀行・証券・保険などの金融業は会計が特殊なのでスキップ

            continue

        v2 = v1[0].split('-')
        repo = v2[1]
        if repo == "asr":
            major_context_names = [ "FilingDateInstant" ] + annual_context_names

        elif repo in [ "q1r", "q2r", "q3r", "q4r" ]:
            major_context_names = [ "FilingDateInstant" ] + quarterly_context_names

        elif repo == "ssr" or repo == "q5r":
            continue
        else:
            print("unknown report", repo, xbrl_file_name)
            continue

        stats_local = [ Counter() for _ in context_names ]
        
        values = [ [""] * len(all_account_ids[ get_context_type(x) ]) for x in major_context_names ]

        # XBRLファイルの内容を読む。
        collect_values(edinetCode, values, major_context_names, stats_local, root)

        # 会計基準の位置
        accounting_standards_idx = filing_date_account_ids.index("jpdei_cor:AccountingStandardsDEI")

        # 提出日時点の位置
        filing_date_instant_idx = major_context_names.index("FilingDateInstant")
        assert filing_date_instant_idx == 0

        # 会計基準
        accounting_standard = values[filing_date_instant_idx][accounting_standards_idx]
        assert accounting_standard != ""

        if repo == "asr":
            # 有価証券報告書の場合

            account_stats = annual_account_stats
        else:
            # 四半期報告書の場合

            account_stats = quarterly_account_stats

        if accounting_standard in account_stats:
            # 会計基準がすでにある場合

            stats_sum = account_stats[accounting_standard]
        else:
            # 初めての会計基準の場合

            stats_sum = [ Counter() for _ in context_names ]
            account_stats[accounting_standard] = stats_sum

        for tmp_sum, tmp in zip(stats_sum, stats_local):
            for s, c in tmp.items():
                tmp_sum[s] += c

        # 主要なコンテキストの種類ごとに
        for idx, context_name in enumerate(major_context_names):
            context_type = get_context_type(context_name)

            if context_type == 0:
                csv_f[context_type].write("%s,%s,%s,%s\n" % (edinetCode, end_date, repo, ",".join(values[idx])) )
            else:
                csv_f[context_type].write("%s,%s,%s,%s,%s\n" % (edinetCode, end_date, repo, context_display_name(context_name), ",".join(values[idx])) )

        cnt += 1
        if cnt % 500 == 0:
            print("cpu-id:%d count:%d" % (cpu_id, cnt))

    # 報告書の種類ごとに
    for report_idx, account_stats in enumerate([annual_account_stats, quarterly_account_stats]):

        # statsをpickleに書く。
        stats_path = '%s/stats-%d-%d.pickle' % (data_path, report_idx, cpu_id)
        with open(stats_path, 'wb') as f:
            pickle.dump(account_stats, f)

    for f in csv_f:
        f.close()

    print("end subprocess  cpu-id:%d  total:%d" % (cpu_id, cnt))

def concatenate_stats(cpu_count):
    """サブプロセスで作ったstatsを１つにまとめる。

    Args:
        cpu_count(int): CPU数
    """
    stats_f = codecs.open("%s/stats.txt" % data_path, 'w', 'utf-8')

    annual_account_stats = {}
    quarterly_account_stats = {}

    # 出現頻度のJSON
    stats_json = {}

    # 報告書の種類ごとに
    for report_idx, report_name in enumerate([ "有価証券報告書", "四半期報告書" ]):

        account_stats = annual_account_stats if report_idx == 0 else quarterly_account_stats

        # CPU-IDに対し
        for cpu_id in range(cpu_count):

            # statsのpickleを読む。
            stats_path = "%s/stats-%d-%d.pickle" % (data_path, report_idx, cpu_id)
            with open(stats_path, 'rb') as f:
                stats_dic_tmp = pickle.load(f)

            os.remove(stats_path)

            # 会計基準ごとに
            for accounting_standard, stats_tmp in stats_dic_tmp.items():

                if accounting_standard in account_stats:
                    stats_sum = account_stats[accounting_standard]
                else:
                    stats_sum = [ Counter() for _ in context_names ]
                    account_stats[accounting_standard] = stats_sum

                # コンテキストの種類ごとに
                for idx, context_name in enumerate(context_names):

                    # 項目ごとに
                    for name, cnt in stats_tmp[idx].items():
                        stats_sum[idx][name] += cnt

        stats_f.write("\n%s\n報告書      : %s\n%s\n" % ('-'*80, report_name, '-'*80) )

        # 報告書の種類ごとの出現頻度のJSON
        report_json = {}
        stats_json[report_name] = report_json

        # 会計基準ごとに
        for accounting_standard, stats in account_stats.items():

            # 会計基準ごとの出現頻度のJSON
            accounting_json = {}
            report_json[accounting_standard] = accounting_json
            
            stats_f.write("\n%s\n会計基準    : %s\n%s\n" % ('-'*60, accounting_standard, '-'*60) )

            # コンテキストの種類ごとに
            for idx, context_name in enumerate(context_names):
                if len(stats[idx]) == 0:
                    continue

                # コンテキストごとの出現頻度のJSON
                context_json = {}
                accounting_json[context_name] = context_json

                stats_f.write("\n%s\nコンテキスト: %s\n%s\n" % ('-'*40, context_display_name(context_name), '-'*40) )
                v = list(sorted(stats[idx].items(), key=lambda x:x[1], reverse=True))

                # 項目ごとに
                for id, cnt in v:

                    # 名前空間とタグ名を得る。
                    ns, tag_name = id.split(':')

                    # 名前空間に対応するスキーマの辞書を得る。
                    assert ns in ns_xsd_dic
                    xsd_dic = ns_xsd_dic[ns]

                    # タグ名に対応する要素を得る。
                    assert tag_name in xsd_dic
                    ele =xsd_dic[tag_name]

                    name = '"%s", # %s | %s | %s' % (id, ele.label, ele.verbose_label, ele.type)

                    stats_f.write("\t%s | %d\n" % (name, cnt))

                    # 出現頻度, ラベル, 冗長ラベル, 型をJSONに保存する。
                    context_json[id] = [cnt, ele.label, ele.verbose_label, ele.type ]

                stats_f.write("\n")

            stats_f.write("\n")

    stats_f.close()

    # 出現頻度をJSONファイルに書く。
    with codecs.open('%s/stats.json' % data_path, 'w', 'utf-8') as f:
        json.dump(stats_json, f, ensure_ascii=False, indent=4)

    write_calc_tree(context_names, ns_xsd_dic, annual_account_stats, quarterly_account_stats)


def concatenate_summary(cpu_count: int):
    """サブプロセスで作ったCSVファイルを１つにまとめる。

    Args:
        cpu_count(int): CPU数
    """
    # ３つのコンテストのタイプに対し
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

    args = sys.argv
    if len(args) == 2:
        assert args[1] == 'fix'

        # 出力する項目がxbrl_table.pyの値で固定の場合
        fixed_ids = True
    else:

        # 前回の実行で作った出現頻度のJSONファイルを使い、出現頻度の高い項目を出力する場合
        fixed_ids = False

        # 出現頻度のJSONファイルを読む。
        read_stats_json()

    # スキーマと名称リンクと計算リンクのファイルを読む。
    ReadAllSchema()

    cpu_count = multiprocessing.cpu_count()
    process_list = []

    # CPUごとにサブプロセスを作って並列処理をする。
    for cpu_id in range(cpu_count):

        p = Process(target=make_summary, args=(fixed_ids, cpu_count, cpu_id, ns_xsd_dic, verbose_label_dic, all_account_ids, filing_date_account_ids))

        process_list.append(p)

        p.start()

    # すべてのサブプロセスが終了するのを待つ。
    for p in process_list:
        p.join()

    concatenate_summary(cpu_count)

    concatenate_stats(cpu_count)

    print('処理を終了しました。  処理時間:%d秒' % int(time.time() - start_time) )
