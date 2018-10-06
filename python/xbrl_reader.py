import os
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import codecs

root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'

label_dics = {}
xsd_dics = {}

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

def splitUrlLabel(text):
    if text[0] == '{':
        i = text.index('}')
        url = text[1:i]
        label = text[i+1:]

        return url, label
    
    return None, None

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

def ReadSchema(is_local, xsd_path, el, xsd_dic):
    url, label = splitUrlLabel(el.tag)

    if label == 'schema':
        target_ns = el.get('targetNamespace')
        target_ns = normUrl(target_ns)
        if is_local:
            local_xsd_url2path[target_ns] = xsd_path
            local_xsd_dics[target_ns] = xsd_dic
        else:
            xsd_url2path[target_ns] = xsd_path
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
        ReadSchema(is_local, xsd_path, child, xsd_dic)

def getAttribs(el):
    attr = {}
    for k, v in el.attrib.items():
        attr_url, attr_label = splitUrlLabel(k)
        attr[attr_label] = v

    return attr

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

                attr = el.attrib
                for k, v in attr.items():
                    attr_url, attr_label = splitUrlLabel(k)
                    if attr_label == 'label':
                        link_labels[v] = el.text
                        break

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


local_context_dic = {}

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

def NoneStr(x):
    if x is None:
        return ""
    else:
        return x

class Context:
    def __init__(self):
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.dimensionNames  = []
        self.members = []

    def toString(self):
        return "%s:%s:%s:%s:%s" % (NoneStr(self.startDate), NoneStr(self.endDate), NoneStr(self.instant), ','.join(self.dimensionNames), ','.join(self.members))

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

taxonomy_tmpl = root_dir + '/data/EDINET/taxonomy/%s/タクソノミ/taxonomy/'

ns_url_dic = {}

def parseNsUrl(ns_url):

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

        base_path = "%s/%s" % (cur_dir, name )
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
        if xsd_path.startswith(cur_dir):
            dic = local_ns_url_dic
        else:
            dic = ns_url_dic

        if ns_url in dic:
            assert dic[ns_url] == xsd_path
        else:
            dic[ns_url] = xsd_path
    
    if ns_url in xsd_url2path:
        assert xsd_url2path[ns_url] == xsd_path
    elif ns_url in local_xsd_url2path:
        assert local_xsd_url2path[ns_url] == xsd_path


    return xsd_path, label_path

def getTitleNsLabel(text):

    v1 = text.split(':')
    assert v1[0] in ns_dic
    ns_url = ns_dic[v1[0]]
    label      = v1[1]

    ele = getElement(ns_url, label)
    title = ele.getTitle()

    return title

def readContext(el, parent, ctx):
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
        title = getTitleNsLabel(dimension)
        if not title in ctx.dimensionNames:
            ctx.dimensionNames.append(title)

        member = getTitleNsLabel(text)

        ctx.members.append(member)

    else:
        assert label in [ "context", "entity", "period", "scenario" ]

    for child in el:
        readContext(child, label, ctx)

ns_dic = {}

def getNameSpace(path):
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

                ns_dic[name] = url                
                
            break
    f.close()

def GetSchemaLabelDic(url):
    url = normUrl(url)
    xsd_path, label_path = parseNsUrl(url)

    xsd_dic = None

    if xsd_path is not None:
        if url in local_xsd_dics:
            xsd_dic = local_xsd_dics[url]

        elif url in xsd_dics:
            xsd_dic = xsd_dics[url]

        elif os.path.exists(xsd_path):
            xsd_dic = {}

            xsd_tree = ET.parse(xsd_path)
            xsd_root = xsd_tree.getroot()
            ReadSchema(False, xsd_path, xsd_root, xsd_dic)
            assert xsd_dics[url] == xsd_dic

    if label_path is not None:
        if label_path.startswith(cur_dir):
            pass

        elif label_path in label_dics:
            pass

        elif os.path.exists(label_path):

            label_tree = ET.parse(label_path)
            label_root = label_tree.getroot()

            resource_dic = {}
            loc_dic = {}
            ReadLabel(label_root, xsd_dic, loc_dic, resource_dic)

            label_dics[label_path] = 1

    return xsd_dic

def getElement(url, label):
    xsd_dic = GetSchemaLabelDic(url)

    assert xsd_dic is not None and label in xsd_dic
    ele = xsd_dic[label]

    return ele

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

dup_dic = {}
context_txt_dic = []

def dumpInst(dt, nest):
    if dt is None:
        print("")
    tab = '    ' * nest
    for k, v in dt.items():
        if v is None:
            pass
        elif type(v) is str:
            logf2.write("%s%s : %s\n" % (tab, k, v))
        else:
            logf2.write("%s%s\n" % (tab, k))
            dumpInst(v, nest + 1)

def dumpSub(inst, el):

    id, url, label, text = parseElement(el)

    if url == "http://www.xbrl.org/2003/instance" and label == "context":

        ctx = Context()

        readContext(el, None, ctx)
        assert len(ctx.dimensionNames) == len(ctx.members)
        for d, m in zip(ctx.dimensionNames, ctx.members):
            s = d + '|' + m
            if not s in context_txt_dic:
                context_txt_dic.append(s)

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


        local_context_dic[id] = ctx
        return False

    # if url in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]:
    if url in [ "http://www.xbrl.org/2003/linkbase" ]:
        pass
    else:

        ele = getElement(url, label)

        assert el.tag[0] == '{'

        context_ref = el.get("contextRef")
        # assert context_ref is not None
        if ele.type is None or context_ref is None:
            return True

        assert context_ref in local_context_dic
        ctx = local_context_dic[context_ref]

        context_txt = ctx.text

        if ele.type == "テキストブロック":
            text = "省略"

        if text is not None and 100 < len(text):
            text = "省略:" + text[:20].replace('\n', ' ')

        if len(ele.calcFrom) != 0:
            
            s = '↑' + '|'.join([ x.to.getTitle() for x in ele.calcFrom ])
            if text is None:
                text = s
            else:
                text += s

        if ctx.time in inst:
            dt = inst[ctx.time]
        else:
            dt = {}
            inst[ctx.time] = dt

        if len(ctx.dimensionNames) != 0:
            for dim, mem in zip(ctx.dimensionNames, ctx.members):
                if dim in dt:
                    ax = dt[dim]
                else:
                    ax = {}
                    dt[dim] = ax

                if mem in ax:
                    dt = ax[mem]
                else:
                    dt = {}
                    ax[mem] = dt

        title = ele.getTitle()
        if title in dt:
            assert dt[title] == text
        else:
            dt[title] = text
        
        logf.write("[%s][%s][%s][%s]\n" % (ele.type, context_txt, title, text))

        if context_txt != '':
            s = context_txt + '|' + title
            t = context_ref + '|' + el.tag
            if s in dup_dic:
                assert dup_dic[s] == t
            else:
                dup_dic[s] = t

    return True

def dump(inst, el):
    go_down = dumpSub(inst, el)

    if go_down:
        for child in el:
            dump(inst, child)

logf =  open(root_dir + '/data/log.txt', 'w', encoding='utf-8')
logf2 =  open(root_dir + '/data/log2.txt', 'w', encoding='utf-8')

xsd_url2path = {}
xbrl_xsd_dic = None

xbrl_idx = 0
report_path = root_dir + '/data/EDINET/四半期報告書'

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

def readCalcSub(el, xsd_dic, locs, arcs):
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
                        if v[0] in xsd_url2path:
                            xsd_dic2 = xsd_dics[ v[0] ]
                        else:
                            xsd_dic2 = GetSchemaLabelDic(v[0])

                    else:
                        xsd_dic2 = xsd_dic
                    assert v[1] in xsd_dic2
                    locs[ attr2['label'] ] = xsd_dic2[ v[1] ]

                elif label2 == 'calculationArc':
                    arcs.append(el2)

    else:
        for child in el:
            readCalcSub(child, xsd_dic, locs, arcs)

def readCalc():
    name_space = 'jppfs'
    name_cor = 'jppfs_cor'
    for yymmdd in [ '2018-02-28' ]:
        xsd_base = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd
        xsd_path = xsd_base + '/' + name_cor + "_" + yymmdd + '.xsd'

        xsd_dic = {}

        ReadSchema(False, xsd_path, ET.parse(xsd_path).getroot(), xsd_dic)

        for xml_path in Path(xsd_base).glob('r/*/*.xml'):
            xml_path = str(xml_path).replace('\\', '/')
            locs = {}
            arcs = []
            readCalcSub(ET.parse(xml_path).getroot(), xsd_dic, locs, arcs)
            readCalcArcs(xsd_dic, locs, arcs)

readCalc()


for category_dir in Path(report_path).glob("*"):
    category_name = os.path.basename(str(category_dir))

    for public_doc in category_dir.glob("*/*/XBRL/PublicDoc"):
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
            if xbrl_idx % 100 == 0:
                print(xbrl_idx, xbrl_path)

            cur_dir = os.path.dirname(xbrl_path).replace('\\', '/')

            local_context_dic = {}

            ns_dic = {}
            link_labels = {}
            dup_dic = {}
            local_xsd_dics = {}
            local_ns_url_dic = {}
            local_xsd_url2path = {}

            local_label_cnt = 0

            if xbrl_xsd_dic is None:
                xbrl_xsd_dic = GetSchemaLabelDic("http://www.xbrl.org/2003/instance")

            for local_xsd_path_obj in Path(cur_dir).glob("*.xsd"):
                local_xsd_path_org = str(local_xsd_path_obj)
                local_xsd_path = local_xsd_path_org.replace('\\', '/')

                local_xsd_dic = {}

                ReadSchema(True, local_xsd_path, ET.parse(local_xsd_path).getroot(), local_xsd_dic)

                local_label_path = local_xsd_path[:len(local_xsd_path) - 4] + "_lab.xml"
                if os.path.exists(local_label_path):

                    resource_dic = {}
                    loc_dic = {}
                    ReadLabel(ET.parse(str(local_label_path)).getroot(), local_xsd_dic, loc_dic, resource_dic)
                    local_label_cnt += 1

                local_cal_path = local_xsd_path[:-4] + '_cal.xml'
                if os.path.exists(local_cal_path):
                    locs = {}
                    arcs = []
                    readCalcSub(ET.parse(local_cal_path).getroot(), local_xsd_dic, locs, arcs)
                    readCalcArcs(local_xsd_dic, locs, arcs)

            local_label_path_list = list( Path(cur_dir).glob("*_lab.xml") )
            assert len(local_label_path_list) == local_label_cnt

            getNameSpace(xbrl_path)

            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            inst = {}
            dump(inst, root)

            for f in [ logf, logf2 ]:
                f.write('\n')
                f.write('------------------------------------------------------------------------------------------\n')
                f.write('%s\n' % xbrl_path)

            dumpInst(inst, 0)

            if not '提出日時点' in inst:
                print(xbrl_path)
                logf.close()
            edinet_code = inst['提出日時点']['EDINETコード、DEI']
            end_date = inst['提出日時点']['当会計期間終了日、DEI']
            json_dir = "%s/data/json/四半期報告書/%s/%s" % (root_dir, category_name, edinet_code)
            if not os.path.exists(json_dir):
                os.makedirs(json_dir)

            json_path = "%s/%s-%s.json" % (json_dir, edinet_code, end_date)
            with codecs.open(json_path,'w','utf-8') as f:
                json_str = json.dumps(inst, ensure_ascii=False)
                f.write(json_str)



logf.write("context_txt_dic --------------------------------------------------\n")
for x in context_txt_dic:
    logf.write(x + '\n')

logf.close()
logf2.close()
