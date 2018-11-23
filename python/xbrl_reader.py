
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
        inf.logf.write('%s %s %d\n' % (name, time_names[k], v))


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

time_names_list = [
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

time_names_order = [x[0] for x in time_names_list]

time_names = dict(x for x in time_names_list)


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
        self.url = None
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
            assert self.url in ['http://www.xbrl.org/2003/instance', 'http://www.w3.org/2001/XMLSchema']

        return self.name, self.label, self.verbose_label


class Context:
    """XBRLのコンテキスト
    """

    def __init__(self):
        self.time = None
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
            self.name = name
            self.label = label
            self.verbose_label = verbose_label

    def copy_name_label(self, union):
        """nameとlabelをコピーする。
        """
        union['name'] = self.name
        union['label'] = self.label
        union['verbose_label'] = self.verbose_label


class ContextNode(XbrlNode):
    """XBRLのコンテキストのツリー構造の中のノード
    """

    def __init__(self, schema):
        super().__init__()

        self.time = None
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.dimensions = []
        self.values = []

        self.set_schema(schema)

    def join_ctx(self, inf, union, cnt, idx):
        """期間別データに単一期間のノードをセットする。
        """
        if self.time is not None:

            if 'time' in union:
                assert union['time'] == self.time
            else:
                union['time'] = self.time

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
            inf.logf.write('union:%s %s %d %s\n' % (self.label, self.text, idx, time_names[inf.time_name]))
            inc_key_cnt(join_cnt, inf.time_name)

        union['children'] = [x.union_item(inf, cnt, idx) for x in self.children]

        return union

    def joinItem(self, inf, ancestors, union, cnt, idx):
        """期間別データに単一期間のデータをセットする。
        """
        assert not self in ancestors
        ancestors.append(self)

        union['text'][idx] = self.text

        if self.schema.type == "金額" and self.label == '原材料及び貯蔵品':
            inf.logf.write('join:%s %s %s\n' % (self.label, self.text, time_names[self.ctx.time]))
            inc_key_cnt(join_cnt, self.ctx.time)

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
        self.to = to_el
        self.role = role
        self.order = order
        self.weight = weight


class Inf:
    __slots__ = ['cpu_count', 'cpu_id', 'cur_dir', 'local_context_dic', 'local_top_context_nodes', 'local_ns_dic',
                 'local_xsd_dics', 'local_url2path', 'local_xsd_url2path', 'logf', 'progress', 'time_name']

    def __init__(self):
        self.cur_dir = None
        self.local_xsd_url2path = None
        self.local_xsd_dics = None
        self.time_name = None

start_time = time.time()
prev_time = start_time
prev_cnt: int = 0

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
report_path = root_dir + '/web/report'

taxonomy_tmpl = root_dir + '/data/EDINET/taxonomy/%s/タクソノミ/taxonomy/'

xbrl_idx = 0
xbrl_basename = None


xsd_dics: Dict[str, SchemaElement] = {}
label_dics: Dict[str, bool] = {}

dmp_cnt: Dict[str, int] = {}
ctx_cnt: Dict[str, int] = {}
join_cnt: Dict[str, int] = {}


def splitUrlLabel(text):
    """テキストをURL部分とラベル部分に分割する。
    例 : {http://www.w3.org/1999/xlink}href
    """
    if text[0] == '{':
        i = text.index('}')
        url = text[1:i]
        label = text[i + 1:]

        return url, label

    return None, None


def getAttribs(el: ET.Element) -> Dict[str, str]:
    """属性のラベルと値の辞書を作って返す。
    """
    # 属性のラベルと値の辞書
    attr: Dict[str, str] = {}

    for k, v in el.attrib.items():
        attr_url, attr_label = splitUrlLabel(k)
        attr[attr_label] = v

    return attr


def parseElement(el: ET.Element):
    """XMLの要素のid, URL, ラベル, テキストを返す。
    :param el:
    :return:
    """
    id = el.get("id")
    text = el.text

    if el.tag[0] == '{':
        i = el.tag.index('}')
        url = el.tag[1:i]
        label = el.tag[i + 1:]
    else:
        url = None
        label = None

    url1, label1 = splitUrlLabel(el.tag)
    assert url1 == url and label1 == label

    return id, url, label, text


def normUrl(url):
    if not url.endswith('.xsd') and url.startswith('http://disclosure.edinet-fsa.go.jp/taxonomy/'):
        v = url.split('/')

        name_space = v[4]
        yymmdd = v[5]
        name_cor = v[6]

        # url : http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2017-02-28/jppfs_cor
        # url2: http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2017-02-28/jppfs_cor_2017-02-28.xsd

        file_name = name_cor + "_" + yymmdd + '.xsd'
        url2 = '/'.join(v[:6]) + '/' + file_name

        return url2

    elif url in [
        'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full',
        'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full',
        'http://xbrl.ifrs.org/taxonomy/2014-03-05/full_ifrs/full_ifrs-cor_2014-03-05.xsd'
    ]:
        return 'http://xbrl.ifrs.org/taxonomy/2015-03-11/full_ifrs/full_ifrs-cor_2015-03-11.xsd'

    else:
        return url


def getTitleNsLabel(inf, text) -> SchemaElement:
    v1 = text.split(':')
    assert v1[0] in inf.local_ns_dic
    ns_url = inf.local_ns_dic[v1[0]]
    label = v1[1]

    ele = getSchemaElement(inf, ns_url, label)

    return ele


def ReadLabel(el, xsd_dic, loc_dic, resource_dic):
    if el.tag[0] == '{':
        i = el.tag.index('}')
        url = el.tag[1:i]
        label = el.tag[i + 1:]

        url1, label1 = splitUrlLabel(el.tag)
        assert url1 == url and label1 == label

        if label == "loc":

            attr = getAttribs(el)
            assert 'href' in attr and 'label' in attr
            # href  = jpcrp040300-q1r-001_E04251-000_2016-06-30_01_2016-08-12.xsd#jpcrp040300-q1r_E04251-000_ProvisionForLossOnCancellationOfContractEL
            # label = ProvisionForLossOnCancellationOfContractEL
            v = attr['href'].split('#')
            assert len(v) == 2
            loc_dic[attr['label']] = v[1]

        elif label == "label":

            attr = getAttribs(el)
            if 'label' in attr and 'role' in attr:
                if attr['role'] in [label_role, verboseLabel_role]:
                    resource_dic[attr['label']] = {'role': attr['role'], 'text': el.text}

            id = el.get("id")
            if id is None:
                # {http://www.xbrl.org/2003/linkbase}label

                return
            # assert id.startswith("label_")

        elif label == "labelArc":
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


def readContext(inf, el: ET.Element, parent_label, ctx: Context):
    """コンテキストの情報を得る。
    """
    id, url, label, text = parseElement(el)

    if label == "identifier":
        assert parent_label == "entity"

    elif label == "startDate":
        assert parent_label == "period"
        ctx.startDate = text
    elif label == "endDate":
        assert parent_label == "period"
        ctx.endDate = text
    elif label == "instant":
        assert parent_label == "period"
        ctx.instant = text

    elif label == "explicitMember":
        assert parent_label == "scenario"

        dimension = el.get("dimension")
        dimension_ele = getTitleNsLabel(inf, dimension)

        assert not dimension_ele in ctx.dimension_schemas

        ctx.dimension_schemas.append(dimension_ele)

        member_schema = getTitleNsLabel(inf, text)

        ctx.member_schemas.append(member_schema)

    else:
        assert label in ["context", "entity", "period", "scenario"]

    for child in el:
        readContext(inf, child, label, ctx)


def setChildren(inf, ctx: ContextNode):
    if len(ctx.dimensions) != 0:
        for dimension in ctx.dimensions:
            for nd in dimension.members:
                setChildren(inf, nd)

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
                inf.logf.write('ctx :%s %s %s\n' % (label, item.text, time_names[ctx.time]))
                inc_key_cnt(ctx_cnt, ctx.time)

    ctx.values = top_items


def readCalcArcs(xsd_dic, locs, arcs):
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
    url, label = splitUrlLabel(el.tag)

    if label == 'schema':
        target_ns = el.get('targetNamespace')
        target_ns = normUrl(target_ns)
        if is_local:
            inf.local_xsd_url2path[target_ns] = xsd_path
            inf.local_xsd_dics[target_ns] = xsd_dic
        else:
            xsd_dics[target_ns] = xsd_dic

    elif label == "element":

        schema = SchemaElement()
        schema.url = url
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


def parseNsUrl(inf, ns_url):
    if ns_url.startswith("http://disclosure.edinet-fsa.go.jp/taxonomy/"):
        # http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2017-02-28/jpcrp_cor

        v2 = ns_url.split('/')
        name_space = v2[4]
        yymmdd = v2[5]
        name_cor = v2[6]

        # '/2013-08-31/タクソノミ/taxonomy/jpdei/2013-08-31/jpdei_cor_2013-08-31.xsd'

        if ns_url.endswith('.xsd'):
            file_name = os.path.basename(ns_url)
        else:
            file_name = name_cor + "_" + yymmdd + '.xsd'
        xsd_path = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/' + file_name
        label_path = (
                             taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/label/' + name_space + "_" + yymmdd + '_lab.xml'

    elif ns_url.startswith("http://disclosure.edinet-fsa.go.jp/"):
        # http://disclosure.edinet-fsa.go.jp/ifrs/q2r/001/E00949-000/2016-09-30/01/2016-11-04
        # http://disclosure.edinet-fsa.go.jp/jpcrp040300/q2r/001/E00949-000/2016-09-30/01/2016-11-04
        # jpcrp040300-q2r-001_E31382-000_2015-07-31_01_2015-09-14.xsd

        v = ns_url[len("http://disclosure.edinet-fsa.go.jp/"):].split('/')
        name = '-'.join(v[:3]) + '_' + '_'.join(v[3:])

        base_path = "%s/%s" % (inf.cur_dir, name)
        xsd_path = base_path + '.xsd'
        label_path = base_path + '_lab.xml'

    elif ns_url.startswith("http://xbrl.ifrs.org/taxonomy/"):
        if ns_url == 'http://xbrl.ifrs.org/taxonomy/2015-03-11/full_ifrs/full_ifrs-cor_2015-03-11.xsd':
            ns_url = 'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full'
        elif ns_url == 'http://xbrl.ifrs.org/taxonomy/2014-03-05/full_ifrs/full_ifrs-cor_2014-03-05.xsd':
            ns_url = 'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full'

        if not ns_url in [
            'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full',
            'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full'
        ]:
            print(ns_url)

        assert ns_url in [
            'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full',
            'http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full'
        ]

        ifrs_path = root_dir + "/data/IFRS/IFRST_%s/full_ifrs/full_ifrs-cor_%s.xsd"

        v = ns_url.split('/')
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

    elif ns_url == "http://www.xbrl.org/2003/instance":
        xsd_path = root_dir + "/data/IFRS/xbrl-instance-2003-12-31.xsd"
        label_path = None

    else:
        assert ns_url in ["http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase"]

        return None, None

    if xsd_path is not None:
        if inf.cur_dir is not None and xsd_path.startswith(inf.cur_dir):
            if ns_url in inf.local_url2path:
                assert inf.local_url2path[ns_url] == xsd_path
            else:
                inf.local_url2path[ns_url] = xsd_path

    elif inf.local_xsd_url2path is not None and ns_url in inf.local_xsd_url2path:
        assert inf.local_xsd_url2path[ns_url] == xsd_path

    return xsd_path, label_path


def makeContext(inf, el, id):
    ctx = Context()

    readContext(inf, el, None, ctx)
    assert len(ctx.dimension_schemas) == len(ctx.member_schemas)

    if len(ctx.dimension_schemas) == 0:

        assert id in time_names
        ctx.time = id

    else:

        k = id.find('_')
        assert k != -1
        s = id[:k]
        assert s in time_names
        ctx.time = s

    nd = find(x for x in inf.local_top_context_nodes if x.time == ctx.time)
    if nd is None:
        nd = ContextNode(None)
        nd.time = ctx.time
        nd.startDate = ctx.startDate
        nd.endDate = ctx.endDate
        nd.instant = ctx.instant

        inf.local_top_context_nodes.append(nd)

    leaf_nd = nd
    for dimension_schema, member_schema in zip(ctx.dimension_schemas, ctx.member_schemas):
        name, label, verbose_label = dimension_schema.getLabel()
        dimensions = [x for x in nd.dimensions if x.name == name]
        if len(dimensions) == 0:
            dimension = Dimension(dimension_schema, name, label, verbose_label)
            nd.dimensions.append(dimension)

        else:
            assert len(dimensions) == 1
            dimension = dimensions[0]

        member_list = [x for x in dimension.members if x.schema == member_schema]
        if len(member_list) != 0:
            assert len(member_list) == 1

            leaf_nd = member_list[0]
        else:

            leaf_nd = ContextNode(member_schema)

            leaf_nd.time = ctx.time
            dimension.members.append(leaf_nd)

        nd = leaf_nd

    assert not id in inf.local_context_dic
    inf.local_context_dic[id] = leaf_nd


def getNameSpace(inf, path):
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
                name = line[k1:k2]

                assert line[k2 + 1] == '"'
                k3 = line.find('"', k2 + 2)
                url = line[k2 + 2:k3]

                inf.local_ns_dic[name] = url

            break
    f.close()


def GetSchemaLabelDic(inf, url) -> Dict[str, SchemaElement]:
    url = normUrl(url)
    xsd_path, label_path = parseNsUrl(inf, url)

    xsd_dic = None

    if xsd_path is not None:
        if inf.local_xsd_dics is not None and url in inf.local_xsd_dics:
            xsd_dic = inf.local_xsd_dics[url]

        else:

            if url in xsd_dics:
                xsd_dic = xsd_dics[url]

            else:
                assert os.path.exists(xsd_path)
                xsd_dic : Dict[str, SchemaElement] = {}

                xsd_tree = ET.parse(xsd_path)
                xsd_root = xsd_tree.getroot()
                ReadSchema(inf, False, xsd_path, xsd_root, xsd_dic)
                assert xsd_dics[url] == xsd_dic

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
                ReadLabel(label_root, xsd_dic, loc_dic, resource_dic)

                label_dics[label_path] = True

    return xsd_dic


def getSchemaElement(inf, url, label) -> SchemaElement:
    xsd_dic = GetSchemaLabelDic(inf, url)

    assert xsd_dic is not None and label in xsd_dic
    ele = xsd_dic[label]

    return ele


def dumpSub(inf, el: ET.Element):
    id, url, label, text = parseElement(el)

    if url == "http://www.xbrl.org/2003/instance" and label == "context":
        makeContext(inf, el, id)
        return False

    # if url in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]:
    if url in ["http://www.xbrl.org/2003/linkbase"]:
        pass
    else:

        ele : SchemaElement = getSchemaElement(inf, url, label)

        assert el.tag[0] == '{'

        context_ref = el.get("contextRef")
        # assert context_ref is not None
        if ele.type is None or context_ref is None:
            return True

        assert context_ref in inf.local_context_dic
        ctx = inf.local_context_dic[context_ref]

        item = Item(ctx, ele, text)
        ctx.values.append(item)

        if ele.type == "金額":
            name, label, verbose_label = ele.getLabel()
            if label == '原材料及び貯蔵品':
                inf.logf.write('dmp :%s %s %s\n' % (label, text, time_names[ctx.time]))
                inc_key_cnt(dmp_cnt, ctx.time)

    return True


def make_tree(inf, el):
    c = el.__class__
    s = el.__class__.__name__
    go_down = dumpSub(inf, el)

    if go_down:
        for child in el:
            make_tree(inf, child)


def readCalcSub(inf, el, xsd_dic, locs, arcs):
    url, label = splitUrlLabel(el.tag)

    if label == 'calculationLink':
        attr = getAttribs(el)
        for el2 in el:
            url2, label2 = splitUrlLabel(el2.tag)
            if label2 in ['loc', 'calculationArc']:
                if label2 == 'loc':
                    attr2 = getAttribs(el2)
                    v = attr2['href'].split('#')
                    if v[0].startswith('http://'):
                        xsd_dic2 = GetSchemaLabelDic(inf, v[0])

                    else:
                        xsd_dic2 = xsd_dic
                    assert v[1] in xsd_dic2
                    locs[attr2['label']] = xsd_dic2[v[1]]

                elif label2 == 'calculationArc':
                    arcs.append(el2)

    else:
        for child in el:
            readCalcSub(inf, child, xsd_dic, locs, arcs)


def readCalc(inf):
    name_space = 'jppfs'
    name_cor = 'jppfs_cor'
    for yymmdd in ['2018-02-28']:
        xsd_base = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd
        xsd_path = xsd_base + '/' + name_cor + "_" + yymmdd + '.xsd'

        xsd_dic = {}

        ReadSchema(inf, False, xsd_path, ET.parse(xsd_path).getroot(), xsd_dic)

        for xml_path in Path(xsd_base).glob('r/*/*.xml'):
            xml_path = str(xml_path).replace('\\', '/')
            locs = {}
            arcs = []
            readCalcSub(inf, ET.parse(xml_path).getroot(), xsd_dic, locs, arcs)
            readCalcArcs(xsd_dic, locs, arcs)


def readXbrl(inf, category_name, public_doc, xbrl_submissions):
    global xbrl_idx, prev_time, prev_cnt, xbrl_basename

    xbrl_list = list(public_doc.glob("*.xbrl"))
    for p in xbrl_list:

        xbrl_path = str(p)
        xbrl_basename = os.path.basename(xbrl_path)
        inf.logf.write('%s ---------------------------------------------------\n' % xbrl_basename)

        if xbrl_basename.startswith('ifrs-'):
            assert len(xbrl_list) == 2
            continue

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

        inf.local_context_dic = {}
        inf.local_top_context_nodes = []

        inf.local_ns_dic = {}
        inf.local_xsd_dics = {}
        inf.local_url2path = {}
        inf.local_xsd_url2path = {}

        label_cnt = 0

        for local_xsd_path_obj in Path(inf.cur_dir).glob("*.xsd"):
            local_xsd_path_org = str(local_xsd_path_obj)
            local_xsd_path = local_xsd_path_org.replace('\\', '/')

            local_xsd_dic = {}

            ReadSchema(inf, True, local_xsd_path, ET.parse(local_xsd_path).getroot(), local_xsd_dic)

            local_label_path = local_xsd_path[:len(local_xsd_path) - 4] + "_lab.xml"
            if os.path.exists(local_label_path):
                resource_dic = {}
                loc_dic = {}
                ReadLabel(ET.parse(str(local_label_path)).getroot(), local_xsd_dic, loc_dic, resource_dic)
                label_cnt += 1

            local_cal_path = local_xsd_path[:-4] + '_cal.xml'
            if os.path.exists(local_cal_path):
                locs = {}
                arcs = []
                readCalcSub(inf, ET.parse(local_cal_path).getroot(), local_xsd_dic, locs, arcs)
                readCalcArcs(local_xsd_dic, locs, arcs)

        local_label_path_list = list(Path(inf.cur_dir).glob("*_lab.xml"))
        assert len(local_label_path_list) == label_cnt

        getNameSpace(inf, xbrl_path)

        tree = ET.parse(xbrl_path)
        root = tree.getroot()
        make_tree(inf, root)

        for ctx in inf.local_top_context_nodes:
            setChildren(inf, ctx)

        ctx_objs = list(inf.local_top_context_nodes)

        dt1 = next(x for x in ctx_objs if x.time == 'FilingDateInstant')  # 提出日時点

        end_date = [x for x in dt1.values if x.name == 'CurrentPeriodEndDateDEI'][0].text  # 当会計期間終了日
        num_submission = next(x for x in dt1.values if x.name == 'NumberOfSubmissionDEI').text  # 提出回数
        document_type = next(x for x in dt1.values if x.name == 'DocumentTypeDEI').text  # 様式

        web_path_len = len(root_dir + '/web/')
        htm_path = [str(x).replace('\\', '/')[web_path_len:] for x in Path(inf.cur_dir).glob("*.htm")]

        revisions = [x for x in xbrl_submissions if x[0] == end_date]
        if any(revisions):

            end_date2, num_submission2, ctx_objs2, htm_path2 = revisions[0]
            if True or num_submission2 < num_submission:
                # json_str_list.remove(x)
                xbrl_submissions.append((end_date, num_submission, ctx_objs, htm_path))

        else:
            xbrl_submissions.append((end_date, num_submission, ctx_objs, htm_path))


def make_public_docs_list(cpu_count):
    category_edinet_codes = []

    public_docs_list = [{} for i in range(cpu_count)]
    for category_dir in Path(report_path).glob("*"):
        category_name = os.path.basename(str(category_dir))

        edinet_codes = []
        category_edinet_codes.append({'category_name': category_name, 'edinet_codes': edinet_codes})

        for public_doc in category_dir.glob("*/*/XBRL/PublicDoc"):
            xbrl_path_list = list(public_doc.glob('jpcrp*.xbrl'))
            assert len(xbrl_path_list) == 1

            xbrl_path_0 = xbrl_path_list[0]
            xbrl_path_0_basename = os.path.basename(str(xbrl_path_0))
            items = re.split('[-_]', xbrl_path_0_basename)
            edinet_code = items[3]
            char_sum = sum(ord(x) for x in edinet_code)
            cpu_idx = char_sum % cpu_count

            dic = public_docs_list[cpu_idx]
            if category_name in dic:
                edinet_code_dic = dic[category_name]
                if edinet_code in edinet_code_dic:
                    edinet_code_dic[edinet_code].append(public_doc)
                else:
                    edinet_code_dic[edinet_code] = [ public_doc ]

            else:
                dic[category_name] = { edinet_code: [public_doc] }

            if not edinet_code in edinet_codes:
                edinet_codes.append(edinet_code)

    json_dir = root_dir + "/web/json"
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    json_path = json_dir + '/category_edinet_codes.json'
    with codecs.open(json_path, 'w', 'utf-8') as json_f:
        json.dump(category_edinet_codes, json_f, ensure_ascii=False)

    return public_docs_list


def readXbrlThread(cpu_count, cpu_id, category_name_dic, progress):
    """スレッドのメイン処理
    """

    inf = Inf()

    inf.cpu_count = cpu_count
    inf.cpu_id = cpu_id
    inf.progress = progress
    inf.logf = open('%s/data/log-%d.txt' % (root_dir, cpu_id), 'w', encoding='utf-8')

    for category_name in category_name_dic.keys():
        json_dir = "%s/web/json/%s" % (root_dir, category_name)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        edinet_code_dic = category_name_dic[category_name]
        for edinet_code, public_docs in edinet_code_dic.items():
            dmp_cnt.clear()
            ctx_cnt.clear()
            join_cnt.clear()

            xbrl_submissions = []
            for public_doc in public_docs:
                readXbrl(inf, category_name, public_doc, xbrl_submissions)

            xbrl_submissions = sorted(xbrl_submissions, key=lambda x: x[0])

            end_date_objs_dic = {}
            for end_date, num_submission, ctx_objs, htm_path in xbrl_submissions:

                for obj in ctx_objs:

                    if obj.time in end_date_objs_dic:
                        end_date_objs_dic[obj.time].append((end_date, obj))
                    else:
                        end_date_objs_dic[obj.time] = [(end_date, obj)]

            time_end_dates_unions = []
            for time_name, end_date_objs in end_date_objs_dic.items():
                inf.time_name = time_name
                union = {}
                time_end_dates = []
                for idx, (end_date, obj) in enumerate(end_date_objs):
                    time_end_dates.append(end_date)
                    obj.join_ctx(inf, union, len(end_date_objs), idx)

                time_end_dates_unions.append((time_name, time_end_dates, union))

            time_end_dates_unions = sorted(time_end_dates_unions, key=lambda x: time_names_order.index(x[0]))

            end_dates = [x[0] for x in xbrl_submissions]

            htm_paths = [x[3] for x in xbrl_submissions]

            doc = {'end_dates': end_dates, 'time_objs': time_end_dates_unions, 'htm_paths': htm_paths}
            with codecs.open('%s/%s.json' % (json_dir, edinet_code), 'w', 'utf-8') as f:
                json.dump(doc, f, ensure_ascii=False)

            log_dict_cnt(inf, 'dmp ', dmp_cnt)
            log_dict_cnt(inf, 'ctx ', ctx_cnt)
            log_dict_cnt(inf, 'join', join_cnt)

            assert len(dmp_cnt) == len(ctx_cnt) and len(dmp_cnt) == len(join_cnt)
            for k, v in dmp_cnt.items():
                assert ctx_cnt[k] == v and join_cnt[k] == v

    inf.logf.close()
    print('CPU:%d 終了:%d' % (cpu_id, int(time.time() - start_time)))


inf = Inf()
readCalc(inf)

GetSchemaLabelDic(inf, "http://www.xbrl.org/2003/instance")

if __name__ == '__main__':
    cpu_count = 1
    cpu_id = 0

    progress = Array('i', [0] * cpu_count)
    public_docs_list = make_public_docs_list(cpu_count)

    readXbrlThread(cpu_count, cpu_id, public_docs_list[cpu_id], progress)
