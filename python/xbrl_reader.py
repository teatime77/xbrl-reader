import os
import xml.etree.ElementTree as ET
from pathlib import Path

root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'

dics = {}
xsd_dics = {}

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
    "nonnum:domainItemType" : "ドメイン"
}

def splitUrlLabel(text):
    if text[0] == '{':
        i = text.index('}')
        url = text[1:i]
        label = text[i+1:]

        return url, label
    
    return None, None

def ReadSchema(el, dic):
    url, label = splitUrlLabel(el.tag)

    if label == "element":

        name = el.get("name")
        type = el.get("type")
        assert type in type_dic
        dic[name] = type_dic[ type ]
                
    for child in el:
        ReadSchema(child, dic)

def ReadLabel(el, dic):
    if el.tag[0] == '{':
        i = el.tag.index('}')
        url = el.tag[1:i]
        label = el.tag[i+1:]
        if label == "label":

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
            dic[name] = el.text
                
    for child in el:
        ReadLabel(child, dic)


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

context_label_dic = []

class Context:
    def __init__(self):
        self.explicitMember = []
        self.startDate = None
        self.endDate = None
        self.instant = None
        self.titles  = []
        self.members = []

taxonomy_tmpl = root_dir + '/data/EDINET/taxonomy/%s/タクソノミ/taxonomy/'
dimension_label_err = []
ns_url_err = []

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

        base_path = root_dir + '/data/EDINET/taxonomy/2018-02-28/タクソノミ/taxonomy/jppfs/2018-02-28/label/jppfs_2018-02-28'
        xsd_path   = base_path + '.xsd'
        label_path = base_path + '_lab.xml'
    else:
        if not ns_url in ns_url_err:
            ns_url_err.append(ns_url)
        return None, None

    return xsd_path, label_path

def getTitleNsLabel(text):
    title = "不明"

    v1 = text.split(':')
    if v1[0] in ns_dic:
        ns_url = ns_dic[v1[0]]
        label      = v1[1]

        xsd_path, label_path = parseNsUrl(ns_url)

        title = getTitle(label_path, label)

    return title

def readContext(el, parent, ctx):
    id, url, label, text = parseElement(el)

    if label is not None and not label in context_label_dic:
        context_label_dic.append(label)

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

        title = getTitleNsLabel(el.get("dimension"))
        if not title in ctx.titles:
            ctx.titles.append(title)

        if (title is None or title == "不明") and not label in dimension_label_err:
            dimension_label_err.append(label)

        member = getTitleNsLabel(text)
        if member == "不明":
            s = text.replace(':', '_') + "_label"
            if s in link_labels:
                member = link_labels[s]

            else:
                v = text.split(':')
                s = v[1]
                if s in ifrs_labels:
                    member = ifrs_labels[s]
                elif s in local_labels:
                    member = local_labels[s]
                else:
                    assert False

        ctx.members.append(member)

    else:
        assert label in [ "context", "entity", "period", "scenario" ]

    for child in el:
        readContext(child, label, ctx)

ns_dic = {}
xsd_path_err = []

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

def getTitle(label_path, label):
    if label_path in dics:
        dic = dics[label_path]
    else:

        if not os.path.exists(label_path):
            # print("label", label_path)

            return "不明"
        assert os.path.exists(label_path)

        label_tree = ET.parse(label_path)
        label_root = label_tree.getroot()

        dic = {}
        ReadLabel(label_root, dic)

        dics[label_path] = dic

    if label in dic:
        title = dic[label]
    else:
        return "不明"

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

ctx_dic = []

def dump(el, nest, logf):
    tab = '  ' * nest

    id, url, label, text = parseElement(el)
    xsd_path, label_path = parseNsUrl(url)

    if el.tag[0] == '{':

        context_ref = el.get("contextRef")
        if context_ref is None:
            context_txt = ""
        else:
            assert context_ref in local_context_dic
            ctx = local_context_dic[context_ref]
            if len(ctx.titles) == 0:

                if context_ref in ctx_names:

                    context_txt = ctx_names[context_ref]
                else:

                    context_txt = context_ref
                    if not context_ref in ctx_name_err:
                        ctx_name_err.append(context_ref)

                if not context_ref in ctx_dic:
                    ctx_dic.append(context_ref)

            else:
                context_txt = ','.join(ctx.titles)

            if len(ctx.members) != 0:
                context_txt += ':' + ','.join(ctx.members)

        if url == "http://www.xbrl.org/2003/instance" and label == "context":
            ctx = Context()
            readContext(el, None, ctx)
            local_context_dic[id] = ctx
            return

        if xsd_path is not None and os.path.exists(xsd_path):

            if xsd_path in xsd_dics:
                xsd_dic = xsd_dics[xsd_path]
            else:
                xsd_dic = {}

                xsd_tree = ET.parse(xsd_path)
                xsd_root = xsd_tree.getroot()
                ReadSchema(xsd_root, xsd_dic)
                xsd_dics[xsd_path] = xsd_dic

            type = xsd_dic[label]

            if type == "nonnum:textBlockItemType":
                text = "省略"
                    
            title = getTitle(label_path, label)
        else:
            if not url in xsd_path_err:
                xsd_path_err.append(url)

            type  = ""
            title = label

        if text is not None and 100 < len(text):
            text = "省略:" + text[:20]

        logf.write("%stag : [%s][%s][%s][%s]\n" % (tab, type, context_txt, title, text))
    else:
        logf.write("%stag : [%s]\n" % (tab, el.tag))
    # print("%s属性" % tab)
    
    for child in el:
        dump(child, nest + 1, logf)

logf =  open('log.txt', 'w', encoding='utf-8')

ifrs_label_path = root_dir + '/data/EDINET/taxonomy/2018-02-28/タクソノミ/taxonomy/jppfs/2018-02-28/label/jppfs_2018-02-28_lab.xml'
ifrs_labels = {}
ReadLabel(ET.parse(ifrs_label_path).getroot(), ifrs_labels)

ctx_name_err = []


report_path = root_dir + '/data/EDINET/四半期報告書'
for category_dir in Path(report_path).glob("*"):
    for p in category_dir.glob("*/*/XBRL/PublicDoc/*.xbrl"):

        path = str(p)
        print("XBRL", path)

        cur_dir = os.path.dirname(path).replace('\\', '/')

        local_context_dic = {}

        ns_dic = {}
        link_labels = {}

        local_labels = {}
        for local_label_path in Path(cur_dir).glob("*_lab.xml"):
            ReadLabel(ET.parse(str(local_label_path)).getroot(), local_labels)

        getNameSpace(path)

        tree = ET.parse(path)
        root = tree.getroot()
        dump(root, 0, logf)

logf.close()


print("context label ----------------------------------------------")
for context_label in context_label_dic:
    print(context_label)


print("dimension label err ----------------------------------------------")
for x in ctx_dic:
    print(x)

print("dimension label err ----------------------------------------------")
for x in dimension_label_err:
    print(x)

print("xsd path err ----------------------------------------------")
for x in xsd_path_err:
    print(x)

print("ns url err ----------------------------------------------")
for x in ns_url_err:
    print(x)

print("ctx name err ----------------------------------------------")
for x in ctx_name_err:
    print(x)
