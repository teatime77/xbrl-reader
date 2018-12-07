
import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import json
import codecs
import threading
import time
from typing import Dict, List, Any
from operator import itemgetter
from multiprocessing import Array
import csv

def read_lines(file_name:str, encoding='utf-8'):
    f = codecs.open(file_name, 'r', encoding, errors='replace')
    lines = [ x.strip() for x in f.readlines() ]
    f.close()

    return lines

def read_csv_file(file_name:str, encoding='utf-8'):
    with codecs.open(file_name, 'r', encoding, errors='replace') as f:
        reader = csv.reader(f)

        lines = [ x for x in reader ]
        # header = next(reader)  # ヘッダーを読み飛ばしたい時

        # for row in reader:
        #     print row          # 1行づつ取得できる

    return lines


def find(search_iteration):
    """リスト内で条件に合う要素を返す。
    """
    try:
        return next(search_iteration)
    except StopIteration:
        return None


def inc_key_cnt(dic: dict, key):
    """指定したキーの値を1つカウントアップする。
    """
    if key in dic:
        dic[key] += 1
    else:
        dic[key] = 1


def log_dict_cnt(inf, name, dic: dict):
    """辞書の値をログファイルに書く。
    """
    for k, v in dic.items():
        inf.logf.write('%s %s %d\n' % (name, period_names[k], v))

category_name_dic = {
    '金属製品' : 'metal',
    '鉱業' : 'mining',
    '鉄鋼' : 'steel',
    'ゴム製品' : 'rubber',
    '非鉄金属' : 'nonferrous_metal',
    '保険業' : 'insurance',
    '電気機器' : 'electronics',
    '倉庫・運輸関連' : 'warehouse_transport',
    'ガラス・土石製品' : 'glass_soil_stone',
    '繊維製品' : 'textile',
    'その他金融業' : 'finance',
    '石油・石炭製品' : 'petroleum_coal',
    '電気・ガス業' : 'electric_power_gas',
    'パルプ・紙' : 'pulp_paper',
    '小売業' : 'retail',
    '輸送用機器' : 'transport_equipment',
    '機械' : 'machinery',
    '証券、商品先物取引業' : 'brokerage',
    '医薬品' : 'pharmaceutical',
    '化学' : 'chemistry',
    '精密機器' : 'precision_instrument',
    '陸運業' : 'land_transport',
    '海運業' : 'marine_transport',
    '空運業' : 'air_transport',
    '不動産業' : 'real_estate',
    '食料品' : 'food',
    '銀行業' : 'bank',
    '卸売業' : 'wholesale',
    'その他製品' : 'other_product',
    '水産・農林業' : 'fishing_agriculture',
    'サービス業' : 'service',
    '建設業' : 'construction',
    '情報・通信業' : 'information_communication',
    '外国政府等' : 'foreign_government',
    '外国法人・組合' : 'foreign_corporation',
    '外国法人・組合（有価証券報告書等の提出義務者以外）' : 'other_foreign_corporation',
    '内国法人・組合（有価証券報告書等の提出義務者以外）' : 'domestic_corporation',
    '個人（組合発行者を除く）' : 'private_person',
    '個人（非居住者）（組合発行者を除く）' : 'private_person_non_resident',
}

# for k,v in category_name_dic.items():
#     print("'%s' : '%s'," % (v,k))

label_role = "http://www.xbrl.org/2003/role/label"
verboseLabel_role = "http://www.xbrl.org/2003/role/verboseLabel"

type_dic = {
    "xbrli:stringItemType": "文字列",
    "xbrli:booleanItemType": "ブール値",
    "xbrli:dateItemType": "日付",
    "xbrli:nonNegativeIntegerItemType": "非負整数",
    "nonnum:textBlockItemType": "テキストブロック",
    "xbrli:monetaryItemType": "金額",
    "num:perShareItemType": "一株当たり金額",
    "num:percentItemType": "割合(%)",
    "xbrli:decimalItemType": "小数",
    "xbrli:sharesItemType": "株数",
    "nonnum:domainItemType": "ドメイン",
    "xbrli:pureItemType": "純粋型"
}

# 報告書インスタンス作成ガイドラインの 5-4-5 コンテキストの設定例
period_names_list = [
    ("FilingDateInstant", "提出日時点"),
    ("CurrentYearInstant", "当期連結時点"),
    ("CurrentYearDuration", "当期連結期間"),
    ("CurrentQuarterInstant", "当四半期会計期間連結時点"),
    ("CurrentQuarterDuration", "当四半期会計期間連結期間"),
    ("CurrentYTDDuration", "当四半期累計期間連結期間"),
    ("Prior1YTDDuration", "前年度同四半期累計期間連結期間"),
    ("Prior1QuarterInstant", "前年度同四半期会計期間連結時点"),
    ("Prior1QuarterDuration", "前年度同四半期会計期間連結期間"),
    ("Prior1YearInstant", "前期連結時点"),
    ("Prior1YearDuration", "前期連結期間"),
    ("Prior2YearInstant", "前々期連結時点"),
    ("Prior2YearDuration", "前々期連結期間"),
    ("Prior3YearInstant", "3期前連結時点"),
    ("Prior3YearDuration", "3期前連結期間"),
    ("Prior4YearInstant", "4期前連結時点"),
    ("Prior4YearDuration", "4期前連結期間"),
    ("Prior2InterimInstant", "Prior2InterimInstant"),
    ("InterimInstant", "InterimInstant"),
    ("InterimDuration", "InterimDuration"),
    ("Prior1InterimInstant", "Prior1InterimInstant"),
    ("Prior1InterimDuration", "Prior1InterimDuration"),
    ("Prior2InterimDuration", "Prior2InterimDuration"),
    ("Prior5YearInstant", "Prior5YearInstant"),
    ("Prior5YearDuration", "Prior5YearDuration"),
]

period_names_order = [x[0] for x in period_names_list]

period_names = dict(x for x in period_names_list)


def findObj(v: dict, key, val):
    """指定したキーの値を返す。
    """

    for x in v:
        if x[key] == val:
            return x
    return None


class SchemaElement:
    """スキーマファイルの中の項目 ( 語彙スキーマ )
    """

    def __init__(self):
        self.uri = None
        self.name = None
        self.id = None
        self.type = None
        self.label = None
        self.verbose_label = None
        self.calcTo = []
        self.sorted = False

    def setLabel(self, role, text):
        if role == label_role:
            self.label = text
        elif role == verboseLabel_role:
            self.verbose_label = text

    def getLabel(self):
        if self.verbose_label is None and self.label is None:
            assert self.uri in ['http://www.xbrl.org/2003/instance', 'http://www.w3.org/2001/XMLSchema']

        return self.name, self.label, self.verbose_label


class Context:
    """XBRLのコンテキスト
    """

    def __init__(self):
        self.period = None
        self.startDate = None
        self.endDate = None
        self.instant = None

        self.dimension_schemas = []
        self.member_schemas = []


class XbrlNode:
    def __init__(self):
        pass

    def set_schema(self, schema):
        """schemaをセットする。
        schemaがNoneでなければ、schemaのnameとlabelを得る。
        """
        self.schema = schema

        if schema is not None:
            name, label, verbose_label = self.schema.getLabel()

            self.name          = name
            self.label         = label
            self.verbose_label = verbose_label

    def copy_name_label(self, union):
        """nameとlabelをコピーする。
        """
        union['name']          = self.name
        union['label']         = self.label
        union['verbose_label'] = self.verbose_label


class ContextNode(XbrlNode):
    """XBRLのコンテキストのツリー構造の中のノード
    """

    def __init__(self, schema):
        super().__init__()

        self.period = None
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.dimensions = []
        self.values = []

        self.set_schema(schema)

    def join_ctx(self, inf, union, cnt, idx):
        """期間別データに単一期間のノードをセットする。
        """
        if self.period is not None:

            if 'period' in union:
                assert union['period'] == self.period
            else:
                union['period'] = self.period

        if self.schema is not None:
            self.copy_name_label(union)

        if len(self.dimensions) != 0:

            if 'dimensions' in union:
                union_dimensions = union['dimensions']
            else:
                union_dimensions = []
                union['dimensions'] = union_dimensions

            for dimension in self.dimensions:

                union_dimension = findObj(union_dimensions, 'name', dimension.name)
                if union_dimension is None:
                    union_dimension = {'members': []}
                    dimension.copy_name_label(union_dimension)
                    union_dimensions.append(union_dimension)

                dimension.join_dimension(inf, union_dimension, cnt, idx)

        if len(self.values) != 0:

            if 'values' in union:
                union_values = union['values']
                for value in self.values:
                    union_value = findObj(union_values, 'name', value.name)
                    if union_value is None:
                        union_values.append(value.union_item(inf, cnt, idx))
                    else:
                        value.joinItem(inf, [], union_value, cnt, idx)

            else:
                union['values'] = [x.union_item(inf, cnt, idx) for x in self.values]


class Item(XbrlNode):
    """XBRLインスタンスの中の開示情報の項目 ( 売上高,利益など )
    """

    def __init__(self, ctx: ContextNode, schema: SchemaElement, text: str):
        super().__init__()
        self.ctx = ctx
        self.text = text
        self.children = []

        self.set_schema(schema)

        if self.text is None:
            self.text = 'null-text'
        else:
            if self.schema.type == "テキストブロック":
                self.text = "省略"
            elif self.schema.type == '文字列':
                self.text = self.text.replace('\n', ' ')

                if 100 < len(self.text):
                    self.text = "省略:" + self.text

    def union_item(self, inf, cnt, idx):
        """期間別データ(期間ごと値を配列に持つオブジェクト)を作る。
        """

        union = {
            'type': self.schema.type,
            'text': [None] * cnt
        }

        self.copy_name_label(union)

        union['text'][idx] = self.text

        if self.schema.type == "金額" and self.label == '原材料及び貯蔵品':
            inf.logf.write('union:%s %s %d %s\n' % (self.label, self.text, idx, period_names[inf.period]))
            inc_key_cnt(join_cnt, inf.period)

        union['children'] = [x.union_item(inf, cnt, idx) for x in self.children]

        return union

    def joinItem(self, inf, ancestors, union, cnt, idx):
        """期間別データに単一期間のデータをセットする。
        """
        assert not self in ancestors
        ancestors.append(self)

        union['text'][idx] = self.text

        if self.schema.type == "金額" and self.label == '原材料及び貯蔵品':
            inf.logf.write('join:%s %s %s\n' % (self.label, self.text, period_names[self.ctx.period]))
            inc_key_cnt(join_cnt, self.ctx.period)

        union_children = union['children']
        for child in self.children:
            union_child = findObj(union_children, 'name', child.name)
            if union_child is None:
                union_children.append(child.union_item(inf, cnt, idx))
            else:
                child.joinItem(inf, ancestors, union_child, cnt, idx)

        ancestors.pop()


class Dimension(XbrlNode):
    """ディメンション軸
    """

    def __init__(self, schema, name, label, verbose_label):
        super().__init__()

        self.name = name
        self.label = label
        self.verbose_label = verbose_label
        self.members = []

        self.set_schema(schema)

    def join_dimension(self, inf, union_dimension: dict, cnt: int, idx: int):
        """期間別データに軸のデータをセットする。
        """
        assert 'name' in union_dimension
        assert union_dimension['name'] == self.name
        assert 'members' in union_dimension

        union_members = union_dimension['members']
        for member in self.members:
            union_member = findObj(union_members, 'name', member.name)
            if union_member is None:
                union_member = {}
                member.copy_name_label(union_member)
                union_members.append(union_member)

            member.join_ctx(inf, union_member, cnt, idx)


class Calc:
    """計算スキーマ
    """

    def __init__(self, to_el, role, order, weight):
        self.to     = to_el
        self.role   = role
        self.order  = order
        self.weight = weight

class Report:
    """報告書
    """
    __slots__ = [ 'end_date', 'num_submission', 'ctx_objs', 'htm_paths' ]

    def __init__(self, end_date, num_submission, ctx_objs, htm_paths):
        self.end_date       = end_date
        self.num_submission = num_submission
        self.ctx_objs       = ctx_objs
        self.htm_paths      = htm_paths

class Inf:
    __slots__ = ['cpu_count', 'cpu_id', 'cur_dir', 'local_node_dic', 'local_top_context_nodes', 'local_ns_dic',
                 'local_xsd_dics', 'local_uri2path', 'local_xsd_uri2path', 'logf', 'progress', 'period']

    def __init__(self):
        self.cur_dir = None
        self.local_xsd_uri2path = None
        self.local_xsd_dics = None
        self.period = None

start_time = time.time()
prev_time = start_time
prev_cnt: int = 0

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
report_path = root_dir + '/web/report'

taxonomy_tmpl = root_dir + '/data/EDINET/taxonomy/%s/taxonomy/'

xbrl_idx = 0
xbrl_basename = None


xsd_dics: Dict[str, SchemaElement] = {}
label_dics: Dict[str, bool] = {}

dmp_cnt: Dict[str, int] = {}
ctx_cnt: Dict[str, int] = {}
join_cnt: Dict[str, int] = {}

def check_taxonomy():
    for date in [ '2013-08-31', '2014-03-31', '2015-03-31', '2016-02-29', '2017-02-28', '2018-02-28' ]:
        xsd_path = '%s/data/EDINET/taxonomy/%s/taxonomy/jppfs/%s/jppfs_cor_%s.xsd' % (root_dir, date, date, date)
        if not os.path.exists(xsd_path):
            print('タクソノミがありません。\n%s' % xsd_path)
            # sys.exit()   

def read_company_dic():

    lines = read_csv_file(root_dir + '/data/EDINET/EdinetcodeDlInfo.csv', 'shift_jis')

    # 最初の2行の見出しは取り除く。
    lines = lines[2:]

    company_dic = dict( (x[0], { 'company_name':x[6], 'category_name': category_name_dic[x[10]] } ) for x in lines if 11 <= len(x) )

    return company_dic

def split_uri_name(text):
    """テキストをURI部分と名前部分に分割する。
    例 : {http://www.xbrl.org/2003/linkbase}calculationArc
    """
    if text[0] == '{':
        i = text.index('}')
        uri = text[1:i]
        tag_name = text[i + 1:]

        return uri, tag_name

    return None, None


def getAttribs(el: ET.Element) -> Dict[str, str]:
    """属性のラベルと値の辞書を作って返す。
    """
    # 属性のラベルと値の辞書
    attr: Dict[str, str] = {}

    for k, v in el.attrib.items():
        attr_uri, attr_name = split_uri_name(k)
        attr[attr_name] = v

    return attr


def parseElement(el: ET.Element):
    """XMLの要素のid, URI, 名前, テキストを返す。
    :param el:
    :return:
    """
    id = el.get("id")

    uri, tag_name = split_uri_name(el.tag)

    return id, uri, tag_name, el.text


def norm_uri(uri):
    """スキーマのURIを正規化する。
    """
    if not uri.endswith('.xsd') and uri.startswith('http://disclosure.edinet-fsa.go.jp/taxonomy/'):
        v = uri.split('/')

        name_space = v[4]
        yymmdd = v[5]
        name_cor = v[6]

        # uri : http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2017-02-28/jppfs_cor
        # uri2: http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2017-02-28/jppfs_cor_2017-02-28.xsd

        file_name = name_cor + "_" + yymmdd + '.xsd'
        uri2 = '/'.join(v[:6]) + '/' + file_name

        return uri2

    elif uri in [
        'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full',
        'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full',
        'http://xbrl.ifrs.org/taxonomy/2014-03-05/full_ifrs/full_ifrs-cor_2014-03-05.xsd'
    ]:
        return 'http://xbrl.ifrs.org/taxonomy/2015-03-11/full_ifrs/full_ifrs-cor_2015-03-11.xsd'

    else:
        return uri


def getSchemaElementNsName(inf, text) -> SchemaElement:
    # 名前空間の接頭辞と要素名に分離する。
    prefix, tag_name = text.split(':')

    # 名前空間の接頭辞をURIに変換する。
    assert prefix in inf.local_ns_dic
    ns_uri = inf.local_ns_dic[prefix]

    # 指定されたURIと名前からスキーマ要素を得る。
    schema = get_schema_element(inf, ns_uri, tag_name)

    return schema


def ReadLabel(el, xsd_dic, loc_dic, resource_dic):
    """名称リンクファイルの内容を読む。
    """
    if el.tag[0] == '{':

        uri, tag_name = split_uri_name(el.tag)

        if tag_name == "loc":

            attr = getAttribs(el)
            assert 'href' in attr and 'label' in attr
            # href  = jpcrp040300-q1r-001_E04251-000_2016-06-30_01_2016-08-12.xsd#jpcrp040300-q1r_E04251-000_ProvisionForLossOnCancellationOfContractEL
            # label = ProvisionForLossOnCancellationOfContractEL
            v = attr['href'].split('#')
            assert len(v) == 2
            loc_dic[attr['label']] = v[1]

        elif tag_name == "label":

            attr = getAttribs(el)
            if 'label' in attr and 'role' in attr:
                if attr['role'] in [label_role, verboseLabel_role]:
                    resource_dic[attr['label']] = {'role': attr['role'], 'text': el.text}

            id = el.get("id")
            if id is None:
                # {http://www.xbrl.org/2003/linkbase}label

                return
            # assert id.startswith("label_")

        elif tag_name == "labelArc":
            if xsd_dic is not None:
                attr = getAttribs(el)

                if 'from' in attr and 'to' in attr and attr['to'] in resource_dic:
                    if attr['from'] in loc_dic and loc_dic[attr['from']] in xsd_dic:
                        ele = xsd_dic[loc_dic[attr['from']]]
                        res = resource_dic[attr['to']]
                        ele.setLabel(res['role'], res['text'])
                    elif attr['from'] in xsd_dic:
                        ele = xsd_dic[attr['from']]
                        res = resource_dic[attr['to']]
                        ele.setLabel(res['role'], res['text'])

    for child in el:
        ReadLabel(child, xsd_dic, loc_dic, resource_dic)

def setChildren(inf, ctx: ContextNode):
    if len(ctx.dimensions) != 0:
        for dimension in ctx.dimensions:
            for member in dimension.members:
                setChildren(inf, member)

    if len(ctx.values) == 0:
        return

    top_items = list(ctx.values)
    for item in ctx.values:

        if not item.schema.sorted:
            item.schema.sorted = True
            item.schema.calcTo = sorted(item.schema.calcTo, key=lambda x: x.order)

        child_elements = [x.to for x in item.schema.calcTo]
        sum_items = [x for x in ctx.values if x.schema in child_elements]
        for sum_item in sum_items:
            if sum_item in top_items:
                item.children.append(sum_item)
                top_items.remove(sum_item)

        if item.schema.type == "金額":
            name, label, verbose_label = item.schema.getLabel()
            if label == '原材料及び貯蔵品':
                inf.logf.write('ctx :%s %s %s\n' % (label, item.text, period_names[ctx.period]))
                inc_key_cnt(ctx_cnt, ctx.period)

    ctx.values = top_items


def readCalcArcs(xsd_dic, locs, arcs):
    """計算リンクの計算関係を得る。
    """
    for el2 in arcs:
        attr2 = getAttribs(el2)
        role = attr2['arcrole']
        if role == 'http://www.xbrl.org/2003/arcrole/summation-item':
            order = el2.get('order')
            weight = el2.get('weight')
            assert order is not None and weight is not None
            order = float(order)

            from_label = attr2['from']
            to_label = attr2['to']
            assert from_label is not None and to_label is not None

            from_el = locs[from_label]
            if to_label in locs:
                to_el = locs[to_label]
            else:
                to_el = xsd_dic[to_label]
            assert from_el is not None and to_el is not None

            if not to_el in [x.to for x in from_el.calcTo]:
                from_el.calcTo.append(Calc(to_el, role, order, weight))


# --------------------------------------------------------------------------------------------------------------

def ReadSchema(inf, is_local, xsd_path, el: ET.Element, xsd_dic: Dict[str, SchemaElement]):
    """スキーマファイルの内容を読む。
    """
    uri, tag_name = split_uri_name(el.tag)

    if tag_name == 'schema':
        target_ns = el.get('targetNamespace')

        # スキーマのURIを正規化する。
        target_ns = norm_uri(target_ns)
        if is_local:
            inf.local_xsd_uri2path[target_ns] = xsd_path
            inf.local_xsd_dics[target_ns] = xsd_dic
        else:
            xsd_dics[target_ns] = xsd_dic

    elif tag_name == "element":

        schema = SchemaElement()
        schema.uri = uri
        schema.name = el.get("name")
        schema.id = el.get("id")

        type = el.get("type")
        if type in type_dic:
            schema.type = type_dic[type]
        else:
            schema.type = type

        xsd_dic[schema.name] = schema

        if schema.id is not None:
            xsd_dic[schema.id] = schema

    for child in el:
        ReadSchema(inf, is_local, xsd_path, child, xsd_dic)


def get_schema_label_path(inf, ns_uri):
    """指定されたURIのスキーマファイルと名称リンクファイルのパスを得る。
    """
    if ns_uri.startswith("http://disclosure.edinet-fsa.go.jp/taxonomy/"):
        # http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2017-02-28/jpcrp_cor

        v2 = ns_uri.split('/')
        name_space = v2[4]
        yymmdd = v2[5]
        name_cor = v2[6]

        # '/2013-08-31/タクソノミ/taxonomy/jpdei/2013-08-31/jpdei_cor_2013-08-31.xsd'

        if ns_uri.endswith('.xsd'):
            file_name = os.path.basename(ns_uri)
        else:
            file_name = name_cor + "_" + yymmdd + '.xsd'
        xsd_path = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/' + file_name
        label_path = (
                             taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/label/' + name_space + "_" + yymmdd + '_lab.xml'

    elif ns_uri.startswith("http://disclosure.edinet-fsa.go.jp/"):
        # http://disclosure.edinet-fsa.go.jp/ifrs/q2r/001/E00949-000/2016-09-30/01/2016-11-04
        # http://disclosure.edinet-fsa.go.jp/jpcrp040300/q2r/001/E00949-000/2016-09-30/01/2016-11-04
        # jpcrp040300-q2r-001_E31382-000_2015-07-31_01_2015-09-14.xsd

        v = ns_uri[len("http://disclosure.edinet-fsa.go.jp/"):].split('/')
        name = '-'.join(v[:3]) + '_' + '_'.join(v[3:])

        base_path = "%s/%s" % (inf.cur_dir, name)
        xsd_path = base_path + '.xsd'
        label_path = base_path + '_lab.xml'

    elif ns_uri.startswith("http://xbrl.ifrs.org/taxonomy/"):
        if ns_uri == 'http://xbrl.ifrs.org/taxonomy/2015-03-11/full_ifrs/full_ifrs-cor_2015-03-11.xsd':
            ns_uri = 'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full'
        elif ns_uri == 'http://xbrl.ifrs.org/taxonomy/2014-03-05/full_ifrs/full_ifrs-cor_2014-03-05.xsd':
            ns_uri = 'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full'

        if not ns_uri in [
            'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full',
            'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full'
        ]:
            print(ns_uri)

        assert ns_uri in [
            'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full',
            'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full'
        ]

        ifrs_path = root_dir + "/data/IFRS/IFRST_%s/full_ifrs/full_ifrs-cor_%s.xsd"

        v = ns_uri.split('/')
        yyyymmdd = v[4]

        xsd_path = ifrs_path % (yyyymmdd, yyyymmdd)
        if not os.path.exists(xsd_path):
            # 2014-03-05が無いので、2015-03-11で代用

            xsd_path = ifrs_path % ('2015-03-11', '2015-03-11')
            assert os.path.exists(xsd_path)

        if yyyymmdd == '2015-03-11':
            label_path = root_dir + '/data/IFRS/ja/Japanese-Taxonomy-2015/full_ifrs/labels/lab_full_ifrs-ja_2015-03-11.xml'
        elif yyyymmdd == '2014-03-05':
            label_path = root_dir + '/data/IFRS/ja/Japanese-Taxonomy-2014/full_ifrs/labels/lab_full_ifrs-ja_2014-03-05_rev_2015-03-06.xml'
        else:
            assert False

    elif ns_uri == "http://www.xbrl.org/2003/instance":
        xsd_path = root_dir + "/data/IFRS/xbrl-instance-2003-12-31.xsd"
        label_path = None

    else:
        assert ns_uri in ["http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase"]

        return None, None

    if xsd_path is not None:
        if inf.cur_dir is not None and xsd_path.startswith(inf.cur_dir):
            if ns_uri in inf.local_uri2path:
                assert inf.local_uri2path[ns_uri] == xsd_path
            else:
                inf.local_uri2path[ns_uri] = xsd_path

    elif inf.local_xsd_uri2path is not None and ns_uri in inf.local_xsd_uri2path:
        assert inf.local_xsd_uri2path[ns_uri] == xsd_path

    return xsd_path, label_path


def readContext(inf, el: ET.Element, parent_tag_name, ctx: Context):
    """コンテキストの情報を得る。
    """
    id, uri, tag_name, text = parseElement(el)

    if tag_name == "identifier":
        assert parent_tag_name == "entity"

    elif tag_name == "startDate":
        assert parent_tag_name == "period"
        ctx.startDate = text
    elif tag_name == "endDate":
        assert parent_tag_name == "period"
        ctx.endDate = text
    elif tag_name == "instant":
        assert parent_tag_name == "period"
        ctx.instant = text

    elif tag_name == "explicitMember":
        assert parent_tag_name == "scenario"

        dimension = el.get("dimension")

        # 次元のスキーマを得る。
        dimension_schema = getSchemaElementNsName(inf, dimension)

        assert not dimension_schema in ctx.dimension_schemas

        ctx.dimension_schemas.append(dimension_schema)

        # メンバーのスキーマを得る。
        member_schema = getSchemaElementNsName(inf, text)

        ctx.member_schemas.append(member_schema)

    else:
        assert tag_name in ["context", "entity", "period", "scenario"]

    # 再帰的にコンテキストの情報を得る。
    for child in el:
        readContext(inf, child, tag_name, ctx)


def makeContextNode(inf, el, id):
    """Contextに対応するContextNodeを作る。
    """
    # コンテキストを作る。
    ctx = Context()

    # コンテキストの情報を得る。
    readContext(inf, el, None, ctx)

    if len(ctx.dimension_schemas) == 0:
        # 次元がない場合

        assert id in period_names
        ctx.period = id

    else:
        # 次元がある場合

        """
        報告書インスタンス作成ガイドライン
            5-4-1 コンテキストIDの命名規約
                {相対期間又は時点}{期間又は時点}((_{メンバーの要素名})×n)(_{連番3桁})
        """

        k = id.find('_')
        assert k != -1
        period_name = id[:k]
        assert period_name in period_names
        ctx.period = period_name

    # ツリー構造のトップノードの中で期間が同じものを探す。
    node = find(x for x in inf.local_top_context_nodes if x.period == ctx.period)
    if node is None:
        # 期間が同じトップノードがない場合

        # トップノードを作る。
        node = ContextNode(None)
        node.period = ctx.period
        node.startDate = ctx.startDate
        node.endDate = ctx.endDate
        node.instant = ctx.instant

        # トップノードのリストに追加する。
        inf.local_top_context_nodes.append(node)

    # 各次元とメンバーの対に対し
    for dimension_schema, member_schema in zip(ctx.dimension_schemas, ctx.member_schemas):
        # 次元の名前,ラベル,冗長ラベルを得る。
        name, label, verbose_label = dimension_schema.getLabel()

        # 名前が同じ次元を探す。
        dimension = find(x for x in node.dimensions if x.name == name)
        if dimension is None:
            # 名前が同じ次元がない場合

            # 次元を作る。
            dimension = Dimension(dimension_schema, name, label, verbose_label)
            node.dimensions.append(dimension)

        # スキーマが同じメンバーを探す。
        leaf_node = find(x for x in dimension.members if x.schema == member_schema)
        if leaf_node is None:
            # スキーマが同じメンバーがない場合

            # メンバーを作る。
            leaf_node = ContextNode(member_schema)

            leaf_node.period = ctx.period
            dimension.members.append(leaf_node)

        node = leaf_node

    # ノードの辞書に追加する。
    assert not id in inf.local_node_dic
    inf.local_node_dic[id] = node


def make_local_ns_dic(inf, path):
    """名前空間の接頭辞とURIの辞書を作る。
    """
    f = open(path)
    for line in f:
        if line.find("xmlns:") != -1:
            k1 = 0
            while True:
                k1 = line.find("xmlns:", k1)
                if k1 == -1:
                    break
                k1 += 6

                k2 = line.find("=", k1)
                prefix = line[k1:k2]

                assert line[k2 + 1] == '"'
                k3 = line.find('"', k2 + 2)
                uri = line[k2 + 2:k3]

                inf.local_ns_dic[prefix] = uri

            break
    f.close()


def get_schema_dic(inf, uri) -> Dict[str, SchemaElement]:
    """指定されたURIのスキーマファイルの辞書を得る。
    辞書がない場合は、スキーマファイルと対応する名称リンクファイルの内容の辞書を作る。
    """

    # スキーマのURIを正規化する。
    uri = norm_uri(uri)

    # 指定されたURIのスキーマファイルと名称リンクファイルのパスを得る。
    xsd_path, label_path = get_schema_label_path(inf, uri)

    xsd_dic = None

    if xsd_path is not None:
        if inf.local_xsd_dics is not None and uri in inf.local_xsd_dics:
            xsd_dic = inf.local_xsd_dics[uri]

        else:

            if uri in xsd_dics:
                xsd_dic = xsd_dics[uri]

            else:
                assert os.path.exists(xsd_path)
                xsd_dic : Dict[str, SchemaElement] = {}

                xsd_tree = ET.parse(xsd_path)
                xsd_root = xsd_tree.getroot()

                # スキーマファイルの内容を読む。
                ReadSchema(inf, False, xsd_path, xsd_root, xsd_dic)
                assert xsd_dics[uri] == xsd_dic

    if label_path is not None:
        if label_path.startswith(inf.cur_dir):
            pass

        else:

            if label_path in label_dics:
                pass

            else:
                assert os.path.exists(label_path)

                label_tree = ET.parse(label_path)
                label_root = label_tree.getroot()

                resource_dic = {}
                loc_dic = {}
                # 名称リンクファイルの内容を読む。
                ReadLabel(label_root, xsd_dic, loc_dic, resource_dic)

                label_dics[label_path] = True

    return xsd_dic


def get_schema_element(inf, uri, tag_name) -> SchemaElement:
    """指定されたURIと名前からスキーマ要素を得る。
    """
    
    # 指定されたURIのスキーマファイルの辞書を得る。
    xsd_dic = get_schema_dic(inf, uri)

    # 辞書と名前からスキーマ要素を得る。
    assert xsd_dic is not None and tag_name in xsd_dic
    schema = xsd_dic[tag_name]

    return schema


def read_xbrl(inf, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)

    if uri == "http://www.xbrl.org/2003/instance" and tag_name == "context":

        # Contextに対応するContextNodeを作る。
        makeContextNode(inf, el, id)
        return

    # if uri in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]:
    if uri in ["http://www.xbrl.org/2003/linkbase"]:
        pass
    else:

        # 指定されたURIと名前からスキーマ要素を得る。
        schema : SchemaElement = get_schema_element(inf, uri, tag_name)

        assert el.tag[0] == '{'

        context_ref = el.get("contextRef")
        # assert context_ref is not None
        if schema.type is not None and context_ref is not None:

            # コンテスト参照からノードを得る。
            assert context_ref in inf.local_node_dic
            node = inf.local_node_dic[context_ref]

            # XBRLインスタンスの中の開示情報の項目を作る。
            item = Item(node, schema, text)

            # ノードの値に項目を追加する。
            node.values.append(item)

            if schema.type == "金額":
                name, label, verbose_label = schema.getLabel()
                if label == '原材料及び貯蔵品':
                    inf.logf.write('dmp :%s %s %s\n' % (label, text, period_names[node.period]))
                    inc_key_cnt(dmp_cnt, node.period)

    # 再帰的にXBRLファイルの内容を読む。
    for child in el:
        read_xbrl(inf, child)


def readCalcSub(inf, el, xsd_dic, locs, arcs):
    """計算リンクファイルの内容を読む。
    """
    uri, tag_name = split_uri_name(el.tag)

    if tag_name == 'calculationLink':
        attr = getAttribs(el)
        for el2 in el:
            uri2, tag_name2 = split_uri_name(el2.tag)
            if tag_name2 == 'loc':
                attr2 = getAttribs(el2)
                v = attr2['href'].split('#')
                if v[0].startswith('http://'):

                    # 指定されたURIのスキーマファイルの辞書を得る。
                    xsd_dic2 = get_schema_dic(inf, v[0])

                else:
                    xsd_dic2 = xsd_dic
                assert v[1] in xsd_dic2
                locs[attr2['label']] = xsd_dic2[v[1]]

            elif tag_name2 == 'calculationArc':
                arcs.append(el2)

    else:
        # 再帰的に計算リンクファイルの内容を読む。
        for child in el:

            # 計算リンクの計算関係を得る。
            readCalcSub(inf, child, xsd_dic, locs, arcs)


def readCalc(inf):
    """計算リンクファイルを読む。
    """
    print('read cal...')
    name_space = 'jppfs'
    name_cor = 'jppfs_cor'
    for yymmdd in ['2018-02-28']:
        xsd_base = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd
        xsd_path = xsd_base + '/' + name_cor + "_" + yymmdd + '.xsd'

        xsd_dic = {}

        # スキーマファイルの内容を読む。
        ReadSchema(inf, False, xsd_path, ET.parse(xsd_path).getroot(), xsd_dic)

        # フォルダーの下の計算リンクファイルに対し
        for xml_path_obj in Path(xsd_base).glob('r/*/*_cal_*.xml'):
            xml_path = str(xml_path_obj).replace('\\', '/')
            locs = {}
            arcs = []

            # 計算リンクファイルの内容を読む。
            readCalcSub(inf, ET.parse(xml_path).getroot(), xsd_dic, locs, arcs)

            # 計算リンクの計算関係を得る。
            readCalcArcs(xsd_dic, locs, arcs)
    
    print('read cal end')


def read_public_doc(inf, category_name, public_doc, reports):
    """XBRLフォルダー内のファイルを読む。
    """
    global xbrl_idx, prev_time, prev_cnt, xbrl_basename

    xbrl_path_obj = find(public_doc.glob('jpcrp*.xbrl'))
    assert xbrl_path_obj is not None

    xbrl_path = str(xbrl_path_obj)
    xbrl_basename = os.path.basename(xbrl_path)
    inf.logf.write('%s ---------------------------------------------------\n' % xbrl_basename)

    # if xbrl_basename != 'jpcrp040300-q2r-001_E03369-000_2016-09-30_01_2016-11-14.xbrl':
    #     continue

    xbrl_idx += 1
    inf.progress[inf.cpu_id] = xbrl_idx
    if xbrl_idx % 100 == 0:
        cnt = sum(inf.progress)
        lap = "%d" % int(1000 * (time.time() - prev_time) / (cnt - prev_cnt))
        prev_time = time.time()
        prev_cnt = cnt
        print(inf.cpu_id, lap, cnt, category_name)

    inf.cur_dir = os.path.dirname(xbrl_path).replace('\\', '/')

    inf.local_node_dic = {}
    inf.local_top_context_nodes = []

    inf.local_ns_dic = {}
    inf.local_xsd_dics = {}
    inf.local_uri2path = {}
    inf.local_xsd_uri2path = {}

    label_cnt = 0

    # フォルダー内のxsdファイルに対し
    for local_xsd_path_obj in Path(inf.cur_dir).glob("*.xsd"):
        local_xsd_path_org = str(local_xsd_path_obj)
        local_xsd_path = local_xsd_path_org.replace('\\', '/')

        local_xsd_dic = {}

        # スキーマファイルの内容を読む。
        ReadSchema(inf, True, local_xsd_path, ET.parse(local_xsd_path).getroot(), local_xsd_dic)

        # 名称リンクファイルのパス
        local_label_path = local_xsd_path[:len(local_xsd_path) - 4] + "_lab.xml"
        if os.path.exists(local_label_path):
            # 名称リンクファイルがある場合

            resource_dic = {}
            loc_dic = {}
            # 名称リンクファイルの内容を読む。
            ReadLabel(ET.parse(str(local_label_path)).getroot(), local_xsd_dic, loc_dic, resource_dic)
            label_cnt += 1

        # 計算ファイルのパス
        local_cal_path = local_xsd_path[:-4] + '_cal.xml'
        if os.path.exists(local_cal_path):
            locs = {}
            arcs = []

            # 計算リンクファイルの内容を読む。
            readCalcSub(inf, ET.parse(local_cal_path).getroot(), local_xsd_dic, locs, arcs)

            # 計算リンクの計算関係を得る。
            readCalcArcs(local_xsd_dic, locs, arcs)

    local_label_path_list = list(Path(inf.cur_dir).glob("*_lab.xml"))
    assert len(local_label_path_list) == label_cnt

    # 名前空間の接頭辞とURIの辞書を作る。
    make_local_ns_dic(inf, xbrl_path)

    # XBRLファイルの内容を読む。
    read_xbrl(inf, ET.parse(xbrl_path).getroot())

    for ctx in inf.local_top_context_nodes:
        setChildren(inf, ctx)

    ctx_objs = list(inf.local_top_context_nodes)

    dt1 = next(x for x in ctx_objs if x.period == 'FilingDateInstant')  # 提出日時点

    end_date = [x for x in dt1.values if x.name == 'CurrentPeriodEndDateDEI'][0].text  # 当会計期間終了日
    num_submission = next(x for x in dt1.values if x.name == 'NumberOfSubmissionDEI').text  # 提出回数
    document_type = next(x for x in dt1.values if x.name == 'DocumentTypeDEI').text  # 様式

    web_path_len = len(root_dir + '/web/')
    htm_paths = [str(x).replace('\\', '/')[web_path_len:] for x in Path(inf.cur_dir).glob("*.htm")]

    # 報告書
    report = Report(end_date, num_submission, ctx_objs, htm_paths)

    # 当会計期間終了日が同じ報告書のリスト ( 訂正報告書の場合 )
    revisions = [x for x in reports if x.end_date == end_date]
    if any(revisions):
        # 当会計期間終了日が同じ報告書がある場合

        report2 = revisions[0]
        if True or report2.num_submission < num_submission:
            # 提出回数の値が大きい場合

            # json_str_list.remove(x)
            reports.append(report)

    else:
        # 当会計期間終了日が同じ報告書がない場合

        reports.append(report)


def make_public_docs_list(cpu_count, company_dic):
    # カテゴリー別の会社リスト
    category_companies = []

    # EDINETコード別のXBRLフォルダーの辞書を各CPUごとに作る。
    public_docs_list = [{} for i in range(cpu_count)]

    # カテゴリー内の'XBRL/PublicDoc'のフォルダーに対し
    for public_doc in Path(report_path).glob("**/XBRL/PublicDoc"):

        # jpcrpのxbrlファイルを得る。( ifrsのxbrlファイルは使わない。 )
        xbrl_path_list = list(public_doc.glob('jpcrp*.xbrl'))
        # assert len(xbrl_path_list) == 1
        if len(xbrl_path_list) != 1:
            print('jpcrp*.xbrl', str(public_doc))
            continue

        xbrl_path_0 = xbrl_path_list[0]

        # パスの中のファイル名を得る。
        # 'jpcrp040300-q2r-001_E03739-000_2017-09-30_01_2017-11-14.xbrl'
        xbrl_path_0_basename = os.path.basename(str(xbrl_path_0))

        # ファイル名を'-'と'_'で区切る。
        items = re.split('[-_]', xbrl_path_0_basename)

        # EDINETコードを得る。
        edinet_code = items[3]

        # EDINETコードの各文字のUNICODEの合計値
        char_sum = sum(ord(x) for x in edinet_code)

        # このEDINETコードのXBRLを処理するCPUのインデックスを決める。
        cpu_idx = char_sum % cpu_count

        # このCPUのカテゴリー別・EDINETコード別のXBRLフォルダーの辞書
        edinet_code_dic = public_docs_list[cpu_idx]
        
        if edinet_code in edinet_code_dic:
            # このEDINETコードがすでに辞書にある場合

            edinet_code_dic[edinet_code].append(public_doc)
        else:
            # このEDINETコードが辞書にない場合

            edinet_code_dic[edinet_code] = [ public_doc ]


        # カテゴリー名
        company = company_dic[edinet_code]
        category_name = company['category_name']
        company_obj = { 'edinet_code': edinet_code, 'company_name': company['company_name'] } 

        category = find(x for x in category_companies if x['category_name'] == category_name)
        if category is None:

            # カテゴリー別の会社のリストに追加する。
            category_companies.append({ 'category_name': category_name, 'companies': [ company_obj ] })

        else:

            # カテゴリー内の会社リスト
            companies = category['companies']

            if not any(x for x in companies if x['edinet_code'] == edinet_code):
                # カテゴリー内の会社リストにない場合

                companies.append( company_obj )


    # JSONを入れるフォルダー
    json_dir = root_dir + "/web/json"
    if not os.path.exists(json_dir):
        # フォルダーがなければ作る。

        os.makedirs(json_dir)

    # カテゴリー別の会社リストのJSONのパス
    json_path = json_dir + '/category_companies.json'

    # JSONをファイルに書く。
    with codecs.open(json_path, 'w', 'utf-8') as json_f:
        json.dump(category_companies, json_f, ensure_ascii=False)

    # 各CPUごとの、EDINETコード別のXBRLフォルダーの辞書を返す。
    return public_docs_list


def readXbrlThread(cpu_count, cpu_id, edinet_code_dic, progress, company_dic):
    """スレッドのメイン処理
    """

    inf = Inf()

    inf.cpu_count = cpu_count
    inf.cpu_id = cpu_id
    inf.progress = progress
    inf.logf = open('%s/data/log-%d.txt' % (root_dir, cpu_id), 'w', encoding='utf-8')

    # EDINETコードとXBRLフォルダーのリストに対し
    for edinet_code, public_docs in edinet_code_dic.items():

        category_name = company_dic[edinet_code]['category_name']

        # JSONを入れるフォルダー
        json_dir = "%s/web/json/%s" % (root_dir, category_name)

        if not os.path.exists(json_dir):
            # フォルダーがなければ作る。
            os.makedirs(json_dir)

        dmp_cnt.clear()
        ctx_cnt.clear()
        join_cnt.clear()

        reports = []

        # 各XBRLフォルダーに対し
        for public_doc in public_docs:
            
            # XBRLフォルダー内のファイルを読む。
            read_public_doc(inf, category_name, public_doc, reports)

        # 当会計期間終了日でソートする。
        reports = sorted(reports, key=lambda x: x.end_date)

        # 当会計期間終了日とでソートする。
        end_date_objs_dic = {}
        for report in reports:

            # 各期間のデータに対し
            for obj in report.ctx_objs:

                if obj.period in end_date_objs_dic:
                    end_date_objs_dic[obj.period].append((report.end_date, obj))
                else:
                    end_date_objs_dic[obj.period] = [(report.end_date, obj)]

        # 期間別にXBRLデータを結合する。
        xbrl_union = []
        for period, end_date_objs in end_date_objs_dic.items():
            inf.period = period
            union = {}
            end_dates = []
            for idx, (end_date, obj) in enumerate(end_date_objs):
                end_dates.append(end_date)
                obj.join_ctx(inf, union, len(end_date_objs), idx)

            xbrl_union.append((period, end_dates, union))

        # period_names_orderの期間名の順に並べ替える。
        xbrl_union = sorted(xbrl_union, key=lambda x: period_names_order.index(x[0]))

        reports_json = [ { 'end_date':x.end_date, 'htm_paths':x.htm_paths } for x in reports ]

        # JSONデータを作る。
        json_data = { 'reports': reports_json, 'xbrl_union': xbrl_union }

        # JSONデータをファイルに書く。
        with codecs.open('%s/%s.json' % (json_dir, edinet_code), 'w', 'utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)

        log_dict_cnt(inf, 'dmp ', dmp_cnt)
        log_dict_cnt(inf, 'ctx ', ctx_cnt)
        log_dict_cnt(inf, 'join', join_cnt)

        assert len(dmp_cnt) == len(ctx_cnt) and len(dmp_cnt) == len(join_cnt)
        for k, v in dmp_cnt.items():
            assert ctx_cnt[k] == v and join_cnt[k] == v

    inf.logf.close()
    print('CPU:%d 終了:%d' % (cpu_id, int(time.time() - start_time)))


inf = Inf()

# 計算リンクファイルを読む。
readCalc(inf)

# 指定されたURIのスキーマファイルと対応する名称リンクファイルの内容の辞書を作る。
get_schema_dic(inf, "http://www.xbrl.org/2003/instance")

if __name__ == '__main__':
    check_taxonomy()
    company_dic = read_company_dic()
    
    cpu_count = 1
    cpu_id = 0

    progress = Array('i', [0] * cpu_count)
    public_docs_list = make_public_docs_list(cpu_count, company_dic)

    readXbrlThread(cpu_count, cpu_id, public_docs_list[cpu_id], progress, company_dic)
