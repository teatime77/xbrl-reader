import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import codecs
import threading
import time

start_time = time.time()
prev_time  = start_time
prev_cnt   = 0

root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'

taxonomy_tmpl = root_dir + '/data/EDINET/taxonomy/%s/タクソノミ/taxonomy/'

xsd_dics = {}
label_dics = {}

url2path = {}
xbrl_idx = 0

local_context_nodes_list = []

url2path_lock = threading.Lock()

label_role = "http://www.xbrl.org/2003/role/label"
verboseLabel_role = "http://www.xbrl.org/2003/role/verboseLabel"
terseLabel_role = "http://www.xbrl.org/2003/role/terseLabel"

type_dic = {
    "xbrli:stringItemType" : "文字列",
    "xbrli:booleanItemType" : "ブール値",
    "xbrli:dateItemType" : "日付",
    "xbrli:nonNegativeIntegerItemType" : "非負整数",
    "nonnum:textBlockItemType" : "テキストブロック",
    "xbrli:monetaryItemType" : "金額",
    "num:perShareItemType" : "一株当たり金額",
    "num:percentItemType" : "割合(%)",
    "xbrli:decimalItemType" : "小数",
    "xbrli:sharesItemType" : "株数",
    "nonnum:domainItemType" : "ドメイン",
    "xbrli:pureItemType" : "純粋型"
}

ctx_names = {
    "FilingDateInstant":"提出日時点",
    "CurrentYTDDuration":"当四半期累計期間連結期間",
    "CurrentQuarterInstant":"当四半期会計期間連結時点",
    "CurrentQuarterDuration":"当四半期会計期間連結期間",
    "Prior1YTDDuration":"前年度同四半期累計期間連結期間",
    "Prior1QuarterInstant":"前年度同四半期会計期間連結時点",
    "Prior1QuarterDuration":"前年度同四半期会計期間連結期間",
    "CurrentYearInstant" :"当期連結時点",
    "CurrentYearDuration":"当期連結期間",
    "Prior1YearInstant"  :"前期連結時点",
    "Prior1YearDuration" :"前期連結期間",
    "Prior2YearInstant"  :"前々期連結時点",
    "Prior2YearDuration" :"前々期連結期間",
    "Prior3YearInstant"  :"3期前連結時点",
    "Prior3YearDuration" :"3期前連結期間",
    "Prior4YearInstant"  :"4期前連結時点",
    "Prior4YearDuration" :"4期前連結期間",
}


class Item:
    def __init__(self, ele, text):
        self.element = ele
        self.text    = text
        self.children = []

    def toObj(self):
        ele = self.element
        text = self.text
        title = ele.getTitle()

        if text is None:
            text = 'null-text'
        else:
            if ele.type == "テキストブロック":
                text = "省略"
            elif ele.type == '文字列':
                text = text.replace('\n', ' ')

                if 100 < len(text):
                    text = "省略:" + text

        if len(ele.calcFrom) != 0:
            
            s = '↑' + '|'.join([ x.to.getTitle() for x in ele.calcFrom ])
            if text is None:
                text = s
            else:
                text += s

        obj = { 'type': ele.type, 'title': title, 'text': text }
        obj['children'] = [ item2.toObj() for item2 in self.children ]

        return obj


class Context:
    def __init__(self):
        self.time       = None
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.dimensionNames  = []
        self.members = []
        self.text = None

    def toString(self):
        return "%s:%s:%s:%s:%s" % (NoneStr(self.startDate), NoneStr(self.endDate), NoneStr(self.instant), ','.join(self.dimensionNames), ','.join(self.members))


class ContextNode:
    def __init__(self):
        self.time       = None
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.dimensions  = {}
        self.member = None
        self.values  = []
        self.text = None

    def toObj(self):
        obj = {}
        if self.time is not None:
            obj['time'] = self.time

        if self.member is not None:
            obj['member'] = self.member

        if len(self.dimensions) != 0:
            dimensions = {}
            obj['dimensions'] = dimensions
            for dim, ax in self.dimensions.items():
                dimensions[dim] = [ nd.toObj() for mem, nd in ax.items()  ]

        else:

            obj['values'] = [ item.toObj() for item in self.values ]

        return obj

class Element:
    def __init__(self):
        self.url  = None
        self.name = None
        self.id   = None
        self.type = None
        self.labels = {}
        self.calcTo = []
        self.calcFrom = []

    def getTitle(self):
        if verboseLabel_role in self.labels:
            return self.labels[verboseLabel_role]
        elif label_role in self.labels:
            return self.labels[label_role]
        elif terseLabel_role in self.labels:
            return self.labels[terseLabel_role]
        else:
            assert self.url in ['http://www.xbrl.org/2003/instance', 'http://www.w3.org/2001/XMLSchema']
            return self.name


class Calc:
    def __init__(self, to_el, role, order, weight):
        self.to = to_el
        self.role = role
        self.order = order
        self.weight = weight

class Inf:
    __slots__ = [ 'cpu_count', 'cpu_id', 'cur_dir', 'local_context_dic', 'local_context_nodes', 'local_ns_dic', 'local_xsd_dics', 'local_url2path', 'local_xsd_url2path', 'logf', 'progress' ]

    def __init__(self):
        self.cur_dir = None
        self.local_xsd_url2path = None
        self.local_xsd_dics = None

def splitUrlLabel(text):
    if text[0] == '{':
        i = text.index('}')
        url = text[1:i]
        label = text[i+1:]

        return url, label
    
    return None, None

def getAttribs(el):
    attr = {}
    for k, v in el.attrib.items():
        attr_url, attr_label = splitUrlLabel(k)
        attr[attr_label] = v

    return attr

def parseElement(el):

    id = el.get("id")
    text  = el.text

    if el.tag[0] == '{':
        i = el.tag.index('}')
        url = el.tag[1:i]
        label = el.tag[i+1:]
    else:
        url = None
        label = None

    return id, url, label, text

def normUrl(url):
    if not url.endswith('.xsd') and url.startswith('http://disclosure.edinet-fsa.go.jp/taxonomy/'):
        v = url.split('/')

        name_space = v[4]
        yymmdd     = v[5]
        name_cor   = v[6]

        # '/2013-08-31/タクソノミ/taxonomy/jpdei/2013-08-31/jpdei_cor_2013-08-31.xsd'

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

def NoneStr(x):
    if x is None:
        return ""
    else:
        return x

def getTitleNsLabel(inf, text):

    v1 = text.split(':')
    assert v1[0] in inf.local_ns_dic
    ns_url = inf.local_ns_dic[v1[0]]
    label      = v1[1]

    ele = getElement(inf, ns_url, label)
    title = ele.getTitle()

    return title

def ReadLabel(el, xsd_dic, loc_dic, resource_dic):
    if el.tag[0] == '{':
        i = el.tag.index('}')
        url = el.tag[1:i]
        label = el.tag[i+1:]

        if label == "loc":

            attr = getAttribs(el)
            assert 'href' in attr and 'label' in attr
            v = attr['href'].split('#')
            assert len(v) == 2
            loc_dic[ attr['label'] ] = v[1]

        elif label == "label":

            attr = getAttribs(el)
            if 'label' in attr and 'role' in attr:
                if attr['role'] in [ label_role, verboseLabel_role, terseLabel_role ]:
                    resource_dic[ attr['label'] ] = { 'role':attr['role'], 'text': el.text }

            id = el.get("id")
            if id is None:
                # {http://www.xbrl.org/2003/linkbase}label

                return
            # assert id.startswith("label_")

        elif label == "labelArc":
            if xsd_dic is not None:
                attr = getAttribs(el)

                if 'from' in attr and 'to' in attr and attr['to'] in resource_dic:
                    if attr['from'] in loc_dic and loc_dic[ attr['from'] ] in xsd_dic :
                        ele = xsd_dic[ loc_dic[ attr['from'] ] ]
                        res = resource_dic[ attr['to'] ]
                        ele.labels[ res['role'] ] = res['text']
                    elif attr['from'] in xsd_dic:
                        ele = xsd_dic[ attr['from'] ]
                        res = resource_dic[ attr['to'] ]
                        ele.labels[ res['role'] ] = res['text']

    for child in el:
        ReadLabel(child, xsd_dic, loc_dic, resource_dic)


def readContext(inf, el, parent, ctx):
    id, url, label, text = parseElement(el)

    if label == "identifier":
        assert parent == "entity"

    elif label == "startDate":
        assert parent == "period"
        ctx.startDate = text
    elif label == "endDate":
        assert parent == "period"
        ctx.endDate = text
    elif label == "instant":
        assert parent == "period"
        ctx.instant = text

    elif label == "explicitMember":
        assert parent == "scenario"

        dimension = el.get("dimension")
        title = getTitleNsLabel(inf, dimension)
        if not title in ctx.dimensionNames:
            ctx.dimensionNames.append(title)

        member = getTitleNsLabel(inf, text)

        ctx.members.append(member)

    else:
        assert label in [ "context", "entity", "period", "scenario" ]

    for child in el:
        readContext(inf, child, label, ctx)

def dumpItem(inf, item, nest):
    tab = '    ' * nest
    ele = item.element
    text = item.text
    title = ele.getTitle()

    if text is None:
        text = 'null-text'
    else:
        if ele.type == "テキストブロック":
            text = "省略"
        elif ele.type == '文字列':
            text = text.replace('\n', ' ')

            if 100 < len(text):
                text = "省略:" + text

    if len(ele.calcFrom) != 0:
        
        s = '↑' + '|'.join([ x.to.getTitle() for x in ele.calcFrom ])
        if text is None:
            text = s
        else:
            text += s

    inf.logf.write("%s[%s][%s][%s]\n" % (tab, ele.type, title, text))
    for item2 in item.children:
        dumpItem(inf, item2, nest + 1)

def setChildren(inf, ctx):
    if len(ctx.dimensions) != 0:
        for dim, ax in ctx.dimensions.items():
            for mem, nd in ax.items():
                setChildren(inf, nd)

    else:
        assert len(ctx.values) != 0

        top_items = []
        for item in ctx.values:
            parent_elements = [ x.to for x in item.element.calcFrom ]
            sum_items = [ x for x in ctx.values if x.element in parent_elements ]
            if len(sum_items) == 0:
                top_items.append(item)
            else:
                for sum_item in sum_items:
                    sum_item.children.append(item)                    

        ctx.values = top_items


def dumpCtx(inf, ctx, nest):
    inf.logf.write('    ' * nest)
    if ctx.time is not None:
        inf.logf.write('t:%s ' % ctx.time)

    if ctx.member is not None:
        inf.logf.write('m:%s ' % ctx.member)

    inf.logf.write('\n')
    if len(ctx.dimensions) != 0:
        tab = '    ' * (nest + 1)
        for dim, ax in ctx.dimensions.items():
            inf.logf.write('%sd:%s\n' % (tab, dim))
            for mem, nd in ax.items():
                dumpCtx(inf, nd, nest + 2)

    else:

        for item in ctx.values:
            dumpItem(inf, item, nest + 1)

def readCalcArcs(xsd_dic, locs, arcs):
    for el2 in arcs:
        attr2 = getAttribs(el2)
        role = attr2['arcrole']
        if role == 'http://www.xbrl.org/2003/arcrole/summation-item':
            order = el2.get('order')
            weight = el2.get('weight')
            assert order is not None and weight is not None

            from_label = attr2['from'] 
            to_label = attr2['to'] 
            assert from_label is not None and to_label is not None

            from_el = locs[from_label] 
            if to_label in locs:
                to_el = locs[to_label] 
            else:
                to_el = xsd_dic[to_label]
            assert from_el is not None and to_el is not None

            calc = Calc(to_el, role, order, weight)
            from_el.calcTo.append(calc)

            if not from_el in [ x.to for x in to_el.calcFrom ]:
                to_el.calcFrom.append( Calc(from_el, role, order, weight) )

#--------------------------------------------------------------------------------------------------------------

def ReadSchema(inf, is_local, xsd_path, el, xsd_dic):
    url, label = splitUrlLabel(el.tag)

    if label == 'schema':
        target_ns = el.get('targetNamespace')
        target_ns = normUrl(target_ns)
        if is_local:
            inf.local_xsd_url2path[target_ns] = xsd_path
            inf.local_xsd_dics[target_ns] = xsd_dic
        else:
            xsd_dics[target_ns] = xsd_dic

        attr = getAttribs(el)
    elif label == "element":

        ele = Element()
        ele.url  = url
        ele.name = el.get("name")
        ele.id   = el.get("id")

        type = el.get("type")
        if type in type_dic:
            ele.type = type_dic[ type ]
        else:
            ele.type = type

        xsd_dic[ele.name] = ele

        if ele.id is not None:
            xsd_dic[ele.id] = ele
                
    for child in el:
        ReadSchema(inf, is_local, xsd_path, child, xsd_dic)

def parseNsUrl(inf, ns_url):

    if ns_url.startswith("http://disclosure.edinet-fsa.go.jp/taxonomy/"):
        # http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2017-02-28/jpcrp_cor

        v2 = ns_url.split('/')
        name_space = v2[4]
        yymmdd     = v2[5]
        name_cor   = v2[6]

        # '/2013-08-31/タクソノミ/taxonomy/jpdei/2013-08-31/jpdei_cor_2013-08-31.xsd'

        if ns_url.endswith('.xsd'):
            file_name = os.path.basename(ns_url)
        else:
            file_name = name_cor + "_" + yymmdd + '.xsd'
        xsd_path = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/' + file_name
        label_path = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/label/' + name_space + "_" + yymmdd + '_lab.xml'

    elif ns_url.startswith("http://disclosure.edinet-fsa.go.jp/"):
        # http://disclosure.edinet-fsa.go.jp/ifrs/q2r/001/E00949-000/2016-09-30/01/2016-11-04
        # http://disclosure.edinet-fsa.go.jp/jpcrp040300/q2r/001/E00949-000/2016-09-30/01/2016-11-04
        # jpcrp040300-q2r-001_E31382-000_2015-07-31_01_2015-09-14.xsd

        v = ns_url[len("http://disclosure.edinet-fsa.go.jp/"):].split('/')
        name = '-'.join(v[:3]) + '_' + '_'.join(v[3:])

        base_path = "%s/%s" % (inf.cur_dir, name )
        xsd_path   = base_path + '.xsd'
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
        assert ns_url in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]

        return None, None

    if xsd_path is not None:
        if inf.cur_dir is not None and xsd_path.startswith(inf.cur_dir):
            if ns_url in inf.local_url2path:
                assert inf.local_url2path[ns_url] == xsd_path
            else:
                inf.local_url2path[ns_url] = xsd_path
        else:
            url2path_lock.acquire()
            
            if ns_url in url2path:
                assert url2path[ns_url] == xsd_path
            else:
                url2path[ns_url] = xsd_path
            
            url2path_lock.release()
    
    elif inf.local_xsd_url2path is not None and ns_url in inf.local_xsd_url2path:
        assert inf.local_xsd_url2path[ns_url] == xsd_path


    return xsd_path, label_path

def makeContext(inf, el, id):
    ctx = Context()

    readContext(inf, el, None, ctx)
    assert len(ctx.dimensionNames) == len(ctx.members)

    if len(ctx.dimensionNames) == 0:

        assert id in ctx_names
        ctx.time = ctx_names[id]

        ctx.text = ctx.time

    else:

        ctx.time = ""
        k = id.find('_')
        assert k != -1
        s = id[:k]
        assert s in ctx_names
        ctx.time = ctx_names[s] + "."

        context_txt = ','.join(ctx.dimensionNames)

        context_txt += ':' + ','.join(ctx.members)

        ctx.text = ctx.time + context_txt

    v = [ x for x in inf.local_context_nodes if x.time == ctx.time ]
    if len(v) != 0:
        nd = v[0]
    else:
        nd = ContextNode()
        nd.time = ctx.time
        nd.startDate = ctx.startDate
        nd.endDate = ctx.endDate
        nd.instant = ctx.instant

        inf.local_context_nodes.append(nd)

    for dim, mem in zip(ctx.dimensionNames, ctx.members):        
        if dim in nd.dimensions:
            ax = nd.dimensions[dim]
        else:
            ax = {}
            nd.dimensions[dim] = ax

        if mem in ax:
            nd = ax[mem]
        else:
            nd = ContextNode()
            nd.member = mem
            ax[mem] = nd

    nd.text = ctx.text

    inf.local_context_dic[id] = nd


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

def GetSchemaLabelDic(inf, url):
    url = normUrl(url)
    xsd_path, label_path = parseNsUrl(inf, url)

    xsd_dic = None

    if xsd_path is not None:
        if inf.local_xsd_dics is not None and url in inf.local_xsd_dics:
            xsd_dic = inf.local_xsd_dics[url]

        else:

            if url in xsd_dics:
                xsd_dic = xsd_dics[url]

            elif os.path.exists(xsd_path):
                xsd_dic = {}

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

            elif os.path.exists(label_path):

                label_tree = ET.parse(label_path)
                label_root = label_tree.getroot()

                resource_dic = {}
                loc_dic = {}
                ReadLabel(label_root, xsd_dic, loc_dic, resource_dic)

                label_dics[label_path]  = 1


    return xsd_dic

def getElement(inf, url, label):
    xsd_dic = GetSchemaLabelDic(inf, url)

    assert xsd_dic is not None and label in xsd_dic
    ele = xsd_dic[label]

    return ele

def dumpSub(inf, el):

    id, url, label, text = parseElement(el)

    if url == "http://www.xbrl.org/2003/instance" and label == "context":

        makeContext(inf, el, id)
        return False

    # if url in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]:
    if url in [ "http://www.xbrl.org/2003/linkbase" ]:
        pass
    else:

        ele = getElement(inf, url, label)

        assert el.tag[0] == '{'

        context_ref = el.get("contextRef")
        # assert context_ref is not None
        if ele.type is None or context_ref is None:
            return True

        assert context_ref in inf.local_context_dic
        ctx = inf.local_context_dic[context_ref]

        item = Item(ele, text)
        ctx.values.append(item)

    return True

def dump(inf, el):
    go_down = dumpSub(inf, el)

    if go_down:
        for child in el:
            dump(inf, child)

def readCalcSub(inf, el, xsd_dic, locs, arcs):
    url, label = splitUrlLabel(el.tag)

    if label == 'calculationLink':
        attr = getAttribs(el)
        for el2 in el:
            url2, label2 = splitUrlLabel(el2.tag)
            if label2 in [ 'loc', 'calculationArc' ]: 
                if label2 == 'loc': 
                    attr2 = getAttribs(el2)
                    v = attr2['href'].split('#')
                    if v[0].startswith('http://'):
                        xsd_dic2 = GetSchemaLabelDic(inf, v[0])

                    else:
                        xsd_dic2 = xsd_dic
                    assert v[1] in xsd_dic2
                    locs[ attr2['label'] ] = xsd_dic2[ v[1] ]

                elif label2 == 'calculationArc':
                    arcs.append(el2)

    else:
        for child in el:
            readCalcSub(inf, child, xsd_dic, locs, arcs)

def readCalc(inf):
    name_space = 'jppfs'
    name_cor = 'jppfs_cor'
    for yymmdd in [ '2018-02-28' ]:
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

def readXbrl(inf, category_name, public_doc):
    global xbrl_idx, prev_time, prev_cnt, local_context_nodes_list

    xbrl_list = list( public_doc.glob("*.xbrl") )
    for p in xbrl_list:

        xbrl_path = str(p)
        basename = os.path.basename(xbrl_path)
        if basename.startswith('ifrs-'):
            assert len(xbrl_list) == 2
            continue

        # if basename != 'jpcrp040300-q2r-001_E03369-000_2016-09-30_01_2016-11-14.xbrl':
        #     continue

        xbrl_idx += 1
        inf.progress[inf.cpu_id] = xbrl_idx
        if xbrl_idx % 100 == 0:

            cnt = sum(inf.progress)
            lap = "%d" % int(1000 * (time.time() - prev_time) / (cnt - prev_cnt) )
            prev_time = time.time()
            prev_cnt = cnt
            print(inf.cpu_id, lap, cnt, category_name)

        inf.cur_dir = os.path.dirname(xbrl_path).replace('\\', '/')

        inf.local_context_dic = {}
        inf.local_context_nodes = []

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

        local_label_path_list = list( Path(inf.cur_dir).glob("*_lab.xml") )
        assert len(local_label_path_list) == label_cnt

        getNameSpace(inf, xbrl_path)

        tree = ET.parse(xbrl_path)
        root = tree.getroot()
        dump(inf, root)

        for ctx in inf.local_context_nodes:
            setChildren(inf, ctx)

        ctx_objs = []
        for ctx in inf.local_context_nodes:
            # dumpCtx(inf, ctx, 0)
            ctx_objs.append(ctx.toObj())

        json_str = json.dumps(ctx_objs, ensure_ascii=False)
        local_context_nodes_list.append(json_str)

        # edinet_code = inst['提出日時点']['EDINETコード、DEI']
        # end_date = inst['提出日時点']['当会計期間終了日、DEI']
        # json_dir = "%s/data/json/四半期報告書/%s/%s" % (root_dir, category_name, edinet_code)
        # if not os.path.exists(json_dir):
        #     os.makedirs(json_dir)


def readXbrlThread(cpu_count, cpu_id, public_doc_list, progress):
    inf = Inf()
    
    inf.cpu_count = cpu_count
    inf.cpu_id = cpu_id
    inf.progress = progress
    inf.logf =  open('%s/data/log-%d.txt' % (root_dir, cpu_id), 'w', encoding='utf-8')

    cnt = len(public_doc_list)
    span = cnt // cpu_count
    st = cpu_id * span
    ed = st + span if cpu_id != cpu_count - 1 else cnt

    for category_name, public_doc in public_doc_list[st:ed]:
        readXbrl(inf, category_name, public_doc)

    inf.logf.close()

    with codecs.open('%s/data/log-%d.json' % (root_dir, cpu_id), 'w','utf-8') as f:

        f.write('[\n')
        s = ''
        for json_str in local_context_nodes_list:
            f.write('%s%s\n' % (s, json_str))
            s = ','

        f.write(']\n')

    print('CPU:%d 終了:%d' % (cpu_id, int(time.time() - start_time)) )

inf = Inf()
readCalc(inf)

GetSchemaLabelDic(inf, "http://www.xbrl.org/2003/instance")
