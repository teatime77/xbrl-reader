import os
import xml.etree.ElementTree as ET
from pathlib import Path

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


def ReadSchema(is_local, xsd_path, el, xsd_dic):
    url, label = splitUrlLabel(el.tag)

    if label == 'schema':
        target_ns = el.get('targetNamespace')
        if is_local:
            local_xsd_url2path[target_ns] = xsd_path
        else:
            xsd_url2path[target_ns] = xsd_path

        attr = getAttribs(el)
    elif label == "element":

        ele = Element()
        ele.name = el.get("name")
        ele.id   = el.get("id")

        type = el.get("type")
        assert type in type_dic
        ele.type = type_dic[ type ]

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
        self.prefix = ""
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.dimensionNames  = []
        self.members = []

    def toString(self):
        return "%s:%s:%s:%s:%s" % (NoneStr(self.startDate), NoneStr(self.endDate), NoneStr(self.instant), ','.join(self.dimensionNames), ','.join(self.members))

class Element:
    def __init__(self):
        self.name = None
        self.id   = None
        self.type = None
        self.labels = {}

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

        xsd_path = (taxonomy_tmpl % yymmdd) + name_space + '/' + yymmdd + '/' + name_cor + "_" + yymmdd + '.xsd'
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

    title, type = getTitleType(ns_url, label)

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
    xsd_path, label_path = parseNsUrl(url)

    xsd_dic = None

    if xsd_path is not None:
        if xsd_path.startswith(cur_dir):
            xsd_dic = local_xsd_dics[xsd_path]

        elif xsd_path in xsd_dics:
            xsd_dic = xsd_dics[xsd_path]

        elif os.path.exists(xsd_path):
            xsd_dic = {}

            xsd_tree = ET.parse(xsd_path)
            xsd_root = xsd_tree.getroot()
            ReadSchema(False, xsd_path, xsd_root, xsd_dic)
            xsd_dics[xsd_path] = xsd_dic

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

ifrs_errs = []

def getTitleType(url, label):
    xsd_dic = GetSchemaLabelDic(url)

    ele = None
    if xsd_dic is not None and label in xsd_dic:
        ele = xsd_dic[label]

    if ele is not None:
        type = ele.type
        if verboseLabel_role in ele.labels:
            return ele.labels[verboseLabel_role], type
        elif label_role in ele.labels:
            return ele.labels[label_role], type
        elif terseLabel_role in ele.labels:
            return ele.labels[terseLabel_role], type

    s = label + ':' + url
    if not s in ifrs_errs:
        print(s)
        ifrs_errs.append(s)
    # 'http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full':
    assert url.endswith('/ifrs-full')
    for ifrs_url, dic in ifrs_dic.items():
        if label in dic:
            title, type = dic[label]
            assert type in type_dic                
            return title, type_dic[type]

    assert False

ctx_names = {
    "FilingDateInstant":"提出日時点",
    "CurrentYTDDuration":"当四半期累計期間連結期間",
    "Prior1YearDuration":"前期連結期間",
    "CurrentQuarterInstant":"当四半期会計期間連結時点",
    "Prior1YearInstant":"前期連結時点",
    "CurrentQuarterDuration":"当四半期会計期間連結期間",
    "Prior1YTDDuration":"前年度同四半期累計期間連結期間",
    "Prior1QuarterInstant":"前年度同四半期会計期間連結時点",
    "Prior1QuarterDuration":"前年度同四半期会計期間連結期間",
    "Prior2YearInstant":"前々期連結時点",
    "CurrentYearInstant":"当期連結時点"
}

dup_dic = {}

def dump(el, nest, logf):
    tab = '  ' * nest

    id, url, label, text = parseElement(el)

    if url == "http://www.xbrl.org/2003/instance" and label == "context":

        ctx = Context()
        k = id.find('_')
        if k != -1:
            s = id[:k]
            if s in ctx_names:
                ctx.prefix = ctx_names[s] + "."

        readContext(el, None, ctx)
        local_context_dic[id] = ctx
        return

    if url in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]:
        pass
    else:

        title, type = getTitleType(url, label)

        assert el.tag[0] == '{'

        context_ref = el.get("contextRef")
        assert context_ref is not None

        assert context_ref in local_context_dic
        ctx = local_context_dic[context_ref]

        if len(ctx.dimensionNames) == 0:

            assert context_ref in ctx_names
            context_txt = ctx_names[context_ref]

        else:
            context_txt = ','.join(ctx.dimensionNames)

        if len(ctx.members) != 0:
            context_txt += ':' + ','.join(ctx.members)

        context_txt = ctx.prefix + context_txt

        if type == "テキストブロック":
            text = "省略"

        if text is not None and 100 < len(text):
            text = "省略:" + text[:20]

        logf.write("%stag : [%s][%s][%s][%s]\n" % (tab, type, context_txt, title, text))

        if context_txt != '':
            s = context_txt + '|' + title
            t = context_ref + '|' + el.tag
            if s in dup_dic:
                assert dup_dic[s] == t
            else:
                dup_dic[s] = t
    
    for child in el:
        dump(child, nest + 1, logf)

ifrs_dic = {}
def readIFRS():
    f =  open(root_dir + '/data/EDINET/taxonomy/full_ifrs.csv', 'r', encoding='utf-8')
    f.readline()
    while True:
        line = f.readline()
        if line == '':
            break
        line = line.strip()
        if line.startswith('http://xbrl.ifrs.org/'):
            dic = {}
            ifrs_dic[line] = dic

        else:
            v = line.split('\t')
            dic[v[0]] = [ v[3], v[4] ]

    f.close()


readIFRS()

logf =  open(root_dir + '/data/log.txt', 'w', encoding='utf-8')

xsd_url2path = {}

xbrl_idx = 0
report_path = root_dir + '/data/EDINET/四半期報告書'
for category_dir in Path(report_path).glob("*"):
    for p in category_dir.glob("*/*/XBRL/PublicDoc/*.xbrl"):

        path = str(p)
        basename = os.path.basename(path)
        # if basename != 'ifrs-q3r-001_E00949-000_2016-12-31_01_2017-02-10.xbrl':
        #     continue

        # if not basename in [
        #         "jpcrp040300-q1r-001_E31632-000_2018-06-30_01_2018-08-09.xbrl",
        #         "jpcrp040300-q1r-001_E01669-000_2018-06-30_01_2018-08-10.xbrl",
        #         "jpcrp040300-q1r-001_E01624-000_2018-06-30_01_2018-08-10.xbrl"
        #     ]:

        #     continue

        xbrl_idx += 1
        if xbrl_idx % 100 == 0:
            print(xbrl_idx, path)

        cur_dir = os.path.dirname(path).replace('\\', '/')

        local_context_dic = {}

        ns_dic = {}
        link_labels = {}
        dup_dic = {}
        local_xsd_dics = {}
        local_ns_url_dic = {}
        local_xsd_url2path = {}

        local_label_cnt = 0
        for local_xsd_path_obj in Path(cur_dir).glob("*.xsd"):
            local_xsd_path_org = str(local_xsd_path_obj)
            local_xsd_path = local_xsd_path_org.replace('\\', '/')

            local_xsd_dic = {}
            local_xsd_dics[local_xsd_path] = local_xsd_dic

            ReadSchema(True, local_xsd_path, ET.parse(local_xsd_path).getroot(), local_xsd_dic)

            local_label_path = local_xsd_path[:len(local_xsd_path) - 4] + "_lab.xml"
            if os.path.exists(local_label_path):

                resource_dic = {}
                loc_dic = {}
                ReadLabel(ET.parse(str(local_label_path)).getroot(), local_xsd_dic, loc_dic, resource_dic)
                local_label_cnt += 1

        local_label_path_list = list( Path(cur_dir).glob("*_lab.xml") )
        assert len(local_label_path_list) == local_label_cnt

        getNameSpace(path)

        tree = ET.parse(path)
        root = tree.getroot()
        dump(root, 0, logf)

logf.close()

print('ifrs_errs --------------------------------------------------')
for x in ifrs_errs:
    print(x)