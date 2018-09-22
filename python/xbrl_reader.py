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

def ReadSchema(el, xsd_dic):
    url, label = splitUrlLabel(el.tag)

    if label == "element":

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
        ReadSchema(child, xsd_dic)

def getAttribs(el):
    attr = {}
    for k, v in el.attrib.items():
        attr_url, attr_label = splitUrlLabel(k)
        attr[attr_label] = v

    return attr

def ReadLabel(el, xsd_dic, resource_dic, label_dic):
    if el.tag[0] == '{':
        i = el.tag.index('}')
        url = el.tag[1:i]
        label = el.tag[i+1:]
        if label == "label":

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
            assert id.startswith("label_")
            name = id[6:]
            # print("label : [%s][%s][%s][%s]" % (url, label, name, el.text))
            label_dic[name] = el.text

        elif label == "labelArc":
            if xsd_dic is not None:
                attr = getAttribs(el)

                if 'from' in attr and attr['from'] in xsd_dic and 'to' in attr and attr['to'] in resource_dic:
                    ele = xsd_dic[ attr['from'] ]
                    res = resource_dic[ attr['to'] ]
                    ele.labels[ res['role'] ] = res['text']

    for child in el:
        ReadLabel(child, xsd_dic, resource_dic, label_dic)


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
        # http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full

        v = ns_url.split('/')
        ifrs_path = root_dir + "/data/IFRS/IFRST_%s/full_ifrs/full_ifrs-cor_%s.xsd"

        xsd_path = ifrs_path % (v[4], v[4])
        if not os.path.exists(xsd_path):
            logf.write("XSDがないよ。 %s\n" % xsd_path)
            xsd_path = None

        vp = list(Path(cur_dir).glob("ifrs*_lab.xml"))
        assert len(vp) == 1
        label_path = str(vp[0]).replace('\\', '/')


        # xsd_path   = root_dir + '/data/EDINET/taxonomy/2018-02-28/タクソノミ/taxonomy/jppfs/2018-02-28/jppfs_cor_2018-02-28.xsd'
        # label_path = root_dir + '/data/EDINET/taxonomy/2018-02-28/タクソノミ/taxonomy/jppfs/2018-02-28/label/jppfs_2018-02-28_lab.xml'

    else:        
        assert ns_url in [ "http://www.xbrl.org/2003/instance", "http://www.xbrl.org/2003/linkbase" ]

        return None, None

    return xsd_path, label_path

def getTitleNsLabel(text):
    title = "不明"

    v1 = text.split(':')
    if v1[0] in ns_dic:
        ns_url = ns_dic[v1[0]]
        label      = v1[1]

        xsd_path, label_path = parseNsUrl(ns_url)
        xsd_dic, label_dic = GetSchemaLabelDic(xsd_path, label_path)

        title = getTitle(xsd_dic, label_dic, label)

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

        if title == "不明":
            assert dimension.startswith('ifrs-full:')

        member = getTitleNsLabel(text)
        if member == "不明":
            s = text.replace(':', '_') + "_label"
            if s in link_labels:
                member = link_labels[s]

            else:
                member = getTitleNsLabel(text)
                v = text.split(':')
                s = v[1]
                if s in local_label_dic:
                    member = local_label_dic[s]
                else:
                    assert False

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

def GetSchemaLabelDic(xsd_path, label_path):
    xsd_dic = None
    label_dic = None

    if xsd_path is not None:
        if xsd_path.startswith(cur_dir):
            xsd_dic = local_xsd_dics[xsd_path]

        elif xsd_path in xsd_dics:
            xsd_dic = xsd_dics[xsd_path]

        elif os.path.exists(xsd_path):
            xsd_dic = {}

            xsd_tree = ET.parse(xsd_path)
            xsd_root = xsd_tree.getroot()
            ReadSchema(xsd_root, xsd_dic)
            xsd_dics[xsd_path] = xsd_dic

    if label_path is not None:
        if label_path.startswith(cur_dir):
            label_dic = local_label_dics[label_path]

        elif label_path in label_dics:
            label_dic = label_dics[label_path]

        elif os.path.exists(label_path):

            label_tree = ET.parse(label_path)
            label_root = label_tree.getroot()

            label_dic = {}
            resource_dic = {}
            ReadLabel(label_root, xsd_dic, resource_dic, label_dic)

            label_dics[label_path] = label_dic

    return xsd_dic, label_dic

def getTitle(xsd_dic, label_dic, label):
    title = "不明"

    ele = None
    if xsd_dic is not None and label in xsd_dic:
        ele = xsd_dic[label]

    if ele is not None:
        if verboseLabel_role in ele.labels:
            return ele.labels[verboseLabel_role]
        elif label_role in ele.labels:
            return ele.labels[label_role]
        elif terseLabel_role in ele.labels:
            return ele.labels[terseLabel_role]

    if label + '_3' in label_dic:
        title = label_dic[label + '_3']
    elif label + '_2' in label_dic:
        title = label_dic[label + '_2']
    elif label in label_dic:
        title = label_dic[label]

    return title

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
dup_dic2 = {}
skip_labels = []

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

    xsd_path, label_path = parseNsUrl(url)

    xsd_dic, label_dic = GetSchemaLabelDic(xsd_path, label_path)

    assert el.tag[0] == '{'
                
    if xsd_dic is not None and label_dic is not None:

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

        ele = xsd_dic[label]
        type = ele.type

        if type == "テキストブロック":
            text = "省略"

        title = getTitle(xsd_dic, label_dic, label)

        if text is not None and 100 < len(text):
            text = "省略:" + text[:20]

        logf.write("%stag : [%s][%s][%s][%s]\n" % (tab, type, context_txt, title, text))

        if context_txt != '':
            s = context_txt + '|' + title
            t = context_ref + '|' + el.tag
            if s in dup_dic:
                if not s in dup_dic2:
                    v = dup_dic[s]
                    if not t in v:
                        v.append(t)
                        print(s)
                        for x in v:
                            print("  ", x)
            else:
                dup_dic[s] = [t]

    else:
        assert url in [ 
            "http://www.xbrl.org/2003/instance",
            "http://www.xbrl.org/2003/linkbase",
            "http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full",
            "http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full"
        ]

        if not label in skip_labels:
            skip_labels.append(label)
    
    for child in el:
        dump(child, nest + 1, logf)

logf =  open(root_dir + '/data/log.txt', 'w', encoding='utf-8')

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

        print("XBRL", path)

        cur_dir = os.path.dirname(path).replace('\\', '/')

        local_context_dic = {}

        ns_dic = {}
        link_labels = {}
        dup_dic = {}
        local_xsd_dics = {}
        local_label_dics = {}

        local_label_cnt = 0
        for local_xsd_path_obj in Path(cur_dir).glob("*.xsd"):
            local_xsd_path = str(local_xsd_path_obj).replace('\\', '/')

            local_xsd_dic = {}
            local_xsd_dics[local_xsd_path] = local_xsd_dic

            ReadSchema(ET.parse(local_xsd_path).getroot(), local_xsd_dic)

            local_label_path = local_xsd_path[:len(local_xsd_path) - 4] + "_lab.xml"
            if os.path.exists(local_label_path):

                local_label_dic = {}
                local_label_dics[local_label_path] = local_label_dic
                resource_dic = {}
                ReadLabel(ET.parse(str(local_label_path)).getroot(), local_xsd_dic, resource_dic, local_label_dic)
                local_label_cnt += 1

        local_label_path_list = list( Path(cur_dir).glob("*_lab.xml") )
        assert len(local_label_path_list) == local_label_cnt

        getNameSpace(path)

        tree = ET.parse(path)
        root = tree.getroot()
        dump(root, 0, logf)

        for k,v in dup_dic.items():
            if 2 <= len(v):
                dup_dic2[k] = [ basename, v ]


logf.write("skip labels ----------------------------------------------\n")
for x in skip_labels:
    logf.write(x + "\n")

logf.write("dup dic2 ----------------------------------------------\n")
for k,val in dup_dic2.items():
    logf.write(k + "\n")
    basename, v = val[0], val[1]
    logf.write("  " + basename + "\n")
    for x in v:
        logf.write("  " + x + "\n")



logf.close()
