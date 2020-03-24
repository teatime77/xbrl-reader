import os
import codecs

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path    = root_dir + '/python/data'

def dump_ele(tree_f, max_len_dic, ele, nest, processed):
    if not ele in max_len_dic.keys():
        return len(processed)

    if ele in processed:
        if tree_f is not None:
            tree_f.write("%s%s %s *\n" % ("    "*nest, ele.verbose_label, ele.id))
    else:
        processed.add(ele)
        if tree_f is not None:
            tree_f.write("%s%s %s\n" % ("    "*nest, ele.verbose_label, ele.id))

        for x in ele.child_elements:
            dump_ele(tree_f, max_len_dic, x, nest + 1, processed)

    return len(processed)


def set_max_len_parent2(top_items, max_len_dic, ele):
    if len(ele.parents) == 0:
        top_items.add(ele)
        return 0

    if len(ele.parents) == 1:
        return set_max_len_parent(top_items, max_len_dic, ele.parents[0]) + 1

    parent_lens = [ set_max_len_parent(top_items, max_len_dic, x) for x in ele.parents ]
    max_len  = max(parent_lens)

    for parent, parent_len in zip(list(ele.parents), parent_lens):
        if parent_len < max_len:
            assert parent in ele.parents
            ele.parents.remove(parent)

            assert ele in parent.child_elements
            parent.child_elements.remove(ele)

    return max_len + 1

def set_max_len_parent(top_items, max_len_dic, ele):
    if ele in max_len_dic:
        return max_len_dic[ele]

    max_len = set_max_len_parent2(top_items, max_len_dic, ele)

    max_len_dic[ele] = max_len

    return max_len



def write_calc_tree(context_names, ns_xsd_dic, annual_account_stats, quarterly_account_stats, rank = 200):
    instant_account_dic  = set()
    duration_account_dic = set()

    # 報告書の種類ごとに
    for report_name, account_stats in zip([ "有価証券報告書", "四半期報告書" ], [annual_account_stats, quarterly_account_stats]):

        # 会計基準ごとに
        for accounting_standard, stats in account_stats.items():

            # コンテキストの種類ごとに
            for idx, context_name in enumerate(context_names):
                if not context_name.startswith('CurrentYear'):
                    continue

                if 'Instant' in context_name:
                    # 時点の場合

                    dic = instant_account_dic
                else:
                    # 期間の場合
                    assert 'Duration' in context_name

                    dic = duration_account_dic

                counts = list(sorted(stats[idx].items(), key=lambda x:x[1], reverse=True))

                # 頻出上位の項目のみ使う。
                counts = counts[: rank]

                for count in counts:
                    dic.add(count[0])


    instant_account_ids = list(instant_account_dic)
    duration_account_ids = list(duration_account_dic)

    ns_xsd_dic2 = {}
    for ns, dic in ns_xsd_dic.items():
        dic2 = {}
        ns_xsd_dic2[ns] = dic2

        for key, ele in dic.items():
            if key != ele.id:
                continue

            dic2[key] = ele

            if len(ele.calcTo) != 0:
                ele.calcTo = sorted(ele.calcTo, key=lambda x: x.order)
                ele.child_elements = [x.to for x in ele.calcTo]

                for x in ele.child_elements:
                    assert not ele in x.parents
                    x.parents.append(ele)        

    tree_f = codecs.open("%s/calc_tree.txt" % data_path, 'w', 'utf-8')

    for ids, context_name in zip([ instant_account_ids, duration_account_ids ], [ "会計終了時点", "会計期間" ]):
        tree_f.write("\n%s\nコンテスト : %s\n%s\n" % ('-'*80, context_name, '-'*80) )

        all_items = []

        for id in ids:

            ns, tag_name = id.split(':')

            # 名前空間に対応するスキーマの辞書を得る。
            assert ns in ns_xsd_dic2
            xsd_dic = ns_xsd_dic2[ns]

            # タグ名に対応する要素を得る。
            if not tag_name in xsd_dic:
                tag_name = ns + "_" + tag_name
            assert tag_name in xsd_dic
            ele =xsd_dic[tag_name]

            if ele.type in ['stringItemType', 'textBlockItemType', 'dateItemType']:
                continue

            if not ele in all_items:
                all_items.append(ele)

        top_items = set()
        max_len_dic = {}
        for ele in all_items:
            set_max_len_parent(top_items, max_len_dic, ele)

        top_cnts = [ [ele, dump_ele(None, max_len_dic, ele, 0, set())] for ele in top_items ]

        top_cnts = sorted(top_cnts, key=lambda x:x[1], reverse=True)

        for ele, cnt in top_cnts:
            dump_ele(tree_f, max_len_dic, ele, 0, set())

    tree_f.close()
