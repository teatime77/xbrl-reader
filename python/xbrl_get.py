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
from typing import Dict, List, Any
from collections import OrderedDict

from xbrl_reader import Inf, SchemaElement, Calc, init_xbrl_reader, read_company_dic, readXbrlThread, make_public_docs_list, read_lines, parseElement, getAttribs, label_role, verboseLabel_role, find
from xbrl_reader import ReadSchema, ReadLabel, readCalcSub, readCalcArcs, xsd_dics

reports = [ "有価証券報告書", "四半期報告書", "中間期報告書", "IFRS", "USGAAP" ]

account_ids = [
    "jpdei_cor:EDINETCodeDEI", # EDINETコード
    "jpdei_cor:SecurityCodeDEI", # 証券コード 証券コード、DEI stringItemType	17129

    "jpcrp_cor:FilingDateCoverPage", # 提出日 提出日、表紙 dateItemType	17139
    "jpdei_cor:CurrentFiscalYearStartDateDEI", # 当事業年度開始日 当事業年度開始日、DEI dateItemType	17144
    "jpdei_cor:CurrentFiscalYearEndDateDEI", # 当事業年度終了日 当事業年度終了日、DEI dateItemType	17144
    "jpdei_cor:TypeOfCurrentPeriodDEI", # 当会計期間の種類 当会計期間の種類、DEI stringItemType	17144
    "jpdei_cor:CurrentPeriodEndDateDEI", # 当会計期間終了日 当会計期間終了日、DEI dateItemType	17144

    "jpdei_cor:AccountingStandardsDEI", # 会計基準 会計基準、DEI stringItemType	17144
    "jpdei_cor:WhetherConsolidatedFinancialStatementsArePreparedDEI", # 連結決算の有無 連結決算の有無、DEI booleanItemType	17144

    "jpcrp_cor:NumberOfEmployees", # 従業員数 従業員数 nonNegativeIntegerItemType	17326
    "jpcrp_cor:AverageNumberOfTemporaryWorkers", # 平均臨時雇用人員 平均臨時雇用人員 decimalItemType	13216
    "jpcrp_cor:AverageAgeYearsInformationAboutReportingCompanyInformationAboutEmployees", # 平均年齢（年） 平均年齢（年）、提出会社の状況、従業員の状況 decimalItemType	2646
    "jpcrp_cor:AverageLengthOfServiceYearsInformationAboutReportingCompanyInformationAboutEmployees", # 平均勤続年数（年） 平均勤続年数（年）、提出会社の状況、従業員の状況 decimalItemType	2646
    "jpcrp_cor:AverageAnnualSalaryInformationAboutReportingCompanyInformationAboutEmployees", # 平均年間給与 平均年間給与、提出会社の状況、従業員の状況 monetaryItemType	2646

    "jpcrp_cor:NumberOfSharesHeld", # 所有株式数 所有株式数 sharesItemType	17121
    "jpcrp_cor:ShareholdingRatio", # 発行済株式（自己株式を除く。）の総数に対する所有株式数の割合 発行済株式（自己株式を除く。）の総数に対する所有株式数の割合 percentItemType	17120
    "jpcrp_cor:TotalNumberOfIssuedSharesSummaryOfBusinessResults", # 発行済株式総数 発行済株式総数（普通株式）、経営指標等 sharesItemType	17128

    "jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults", # １株当たり純資産額 １株当たり純資産額、経営指標等 perShareItemType	14464
    "jpcrp_cor:CashAndCashEquivalentsSummaryOfBusinessResults", # 現金及び現金同等物の残高 現金及び現金同等物の残高、経営指標等 monetaryItemType	14462
    "jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults", # 自己資本比率 自己資本比率、経営指標等 percentItemType	14461
    "jpcrp_cor:NetAssetsSummaryOfBusinessResults", # 純資産額 純資産額、経営指標等 monetaryItemType	14460
    "jpcrp_cor:TotalAssetsSummaryOfBusinessResults", # 総資産額 総資産額、経営指標等 monetaryItemType	14460
    "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults", # １株当たり当期純利益又は当期純損失（△） １株当たり当期純利益又は当期純損失（△）、経営指標等 perShareItemType	14459
    "jpcrp_cor:PriceEarningsRatioSummaryOfBusinessResults", # 株価収益率 株価収益率、経営指標等 decimalItemType	14458

    "jpcrp_cor:NumberOfConsolidatedSubsidiaries", # 連結子会社の数 連結子会社の数 nonNegativeIntegerItemType	13942

    "jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults", # 自己資本利益率 自己資本利益率、経営指標等 percentItemType	14460
    "jppfs_cor:OrdinaryIncome", # 経常利益又は経常損失（△） 経常利益又は経常損失（△） monetaryItemType	14430
    "jpcrp_cor:DilutedEarningsPerShareSummaryOfBusinessResults", # 潜在株式調整後1株当たり当期純利益 潜在株式調整後1株当たり当期純利益、経営指標等 perShareItemType	14350
    
    "jppfs_cor:Assets",  # 資産 monetaryItemType
    "jppfs_cor:CurrentAssets", # 流動資産 monetaryItemType
    "jppfs_cor:NoncurrentAssets", # 固定資産 monetaryItemType
    "jppfs_cor:PropertyPlantAndEquipment", # 有形固定資産
    "jppfs_cor:IntangibleAssets", # 無形固定資産
    "jppfs_cor:InvestmentsAndOtherAssets", # 投資その他の資産
    "jppfs_cor:Liabilities", # 負債 monetaryItemType
    "jppfs_cor:CurrentLiabilities", # 流動負債
    "jppfs_cor:NoncurrentLiabilities", # 固定負債
    "jppfs_cor:NetAssets", # 純資産 monetaryItemType
    "jppfs_cor:ShareholdersEquity", # 株主資本
    "jppfs_cor:CapitalStock", # 資本金
    "jppfs_cor:CapitalSurplus", # 資本剰余金
    "jppfs_cor:RetainedEarnings", # 利益剰余金
    "jppfs_cor:TreasuryStock", # 自己株式

    "jppfs_cor:IncomeBeforeIncomeTaxes", # 税引前当期純利益又は税引前当期純損失（△） 税引前当期純利益又は税引前当期純損失（△） monetaryItemType	28029
    "jppfs_cor:OperatingIncome", # 営業利益又は営業損失（△） 営業利益又は営業損失（△） monetaryItemType	22619
    "jppfs_cor:NetSales", # 売上高 売上高 monetaryItemType	21993

    "jppfs_cor:ProfitLossAttributableToOwnersOfParent", # 親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△） 親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△） monetaryItemType	21427
    "jppfs_cor:ProfitLoss", # 当期純利益又は当期純損失（△） 当期純利益又は当期純損失（△）（平成26年3月28日財規等改正後） monetaryItemType	21112
    "jppfs_cor:ComprehensiveIncome", # 包括利益 包括利益 monetaryItemType	14009
    "jppfs_cor:SubtotalOpeCF", # 小計 小計、営業活動によるキャッシュ・フロー monetaryItemType	14009
    "jppfs_cor:NetCashProvidedByUsedInOperatingActivities", # 営業活動によるキャッシュ・フロー 営業活動によるキャッシュ・フロー monetaryItemType	14009

    "jppfs_cor:NetCashProvidedByUsedInInvestmentActivities", # 投資活動によるキャッシュ・フロー 投資活動によるキャッシュ・フロー monetaryItemType	14009
    "jppfs_cor:NetIncreaseDecreaseInCashAndCashEquivalents", # 現金及び現金同等物の増減額（△は減少） 現金及び現金同等物の増減額（△は減少） monetaryItemType	14009
    "jppfs_cor:ComprehensiveIncomeAttributableToOwnersOfTheParent", # 親会社株主に係る包括利益 親会社株主に係る包括利益、包括利益 monetaryItemType	14007
    "jppfs_cor:NonOperatingIncome", # 営業外収益 営業外収益 monetaryItemType	14005

    "jppfs_cor:NetCashProvidedByUsedInFinancingActivities", # 財務活動によるキャッシュ・フロー 財務活動によるキャッシュ・フロー monetaryItemType	14004
    "jppfs_cor:IncomeTaxesCurrent", # 法人税、住民税及び事業税 法人税、住民税及び事業税 monetaryItemType	14003
    "jppfs_cor:IncomeTaxes", # 法人税等 法人税等 monetaryItemType	13986
    "jppfs_cor:SellingGeneralAndAdministrativeExpenses", # 販売費及び一般管理費 販売費及び一般管理費 monetaryItemType	13984
    "jppfs_cor:TotalChangesOfItemsDuringThePeriod", # 当期変動額合計 当期変動額合計 monetaryItemType	13980
    "jppfs_cor:NonOperatingExpenses", # 営業外費用 営業外費用 monetaryItemType	13979
    "jppfs_cor:ImpairmentLossEL", # 減損損失 減損損失、特別損失 monetaryItemType	13960
    "jppfs_cor:DepreciationAndAmortizationOpeCF", # 減価償却費 減価償却費、営業活動によるキャッシュ・フロー monetaryItemType	13878
    "jppfs_cor:NetChangesOfItemsOtherThanShareholdersEquity", # 株主資本以外の項目の当期変動額（純額） 株主資本以外の項目の当期変動額（純額） monetaryItemType	13843
    "jppfs_cor:IncomeTaxesDeferred", # 法人税等調整額 法人税等調整額 monetaryItemType	13807
    "jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF", # 売上債権の増減額（△は増加） 売上債権の増減額（△は増加）、営業活動によるキャッシュ・フロー monetaryItemType	13755
    "jppfs_cor:OtherComprehensiveIncome", # その他の包括利益 その他の包括利益 monetaryItemType	13649
    "jppfs_cor:InterestAndDividendsIncomeReceivedOpeCFInvCF", # 利息及び配当金の受取額 利息及び配当金の受取額、営業活動によるキャッシュ・フロー又は投資活動によるキャッシュ・フロー monetaryItemType	13555
    "jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTradeOpeCF", # 仕入債務の増減額（△は減少） 仕入債務の増減額（△は減少）、営業活動によるキャッシュ・フロー monetaryItemType	13498
    "jppfs_cor:GrossProfit", # 売上総利益又は売上総損失（△） 売上総利益又は売上総損失（△） monetaryItemType	13431
    "jppfs_cor:InterestIncomeNOI", # 受取利息 受取利息、営業外収益 monetaryItemType	13370
    "jppfs_cor:CostOfSales", # 売上原価 売上原価 monetaryItemType	13293
    "jppfs_cor:ExtraordinaryLoss", # 特別損失 特別損失 monetaryItemType	13247
    "jppfs_cor:InterestExpensesPaidOpeCFFinCF", # 利息の支払額 利息の支払額、営業活動によるキャッシュ・フロー又は財務活動によるキャッシュ・フロー monetaryItemType	13217
    "jppfs_cor:InterestAndDividendsIncomeOpeCF", # 受取利息及び受取配当金 受取利息及び受取配当金、営業活動によるキャッシュ・フロー monetaryItemType	13105
    "jppfs_cor:DecreaseIncreaseInInventoriesOpeCF", # たな卸資産の増減額（△は増加） たな卸資産の増減額（△は増加）、営業活動によるキャッシュ・フロー monetaryItemType	12852
    "jppfs_cor:ValuationDifferenceOnAvailableForSaleSecuritiesNetOfTaxOCI", # その他有価証券評価差額金 その他有価証券評価差額金（税引後）、その他の包括利益 monetaryItemType	12773
    "jppfs_cor:IncomeTaxesPaidOpeCF", # 法人税等の支払額 法人税等の支払額、営業活動によるキャッシュ・フロー monetaryItemType	12463
    "jppfs_cor:CashDividendsPaidFinCF", # 配当金の支払額 配当金の支払額、財務活動によるキャッシュ・フロー monetaryItemType	12419
    "jppfs_cor:PurchaseOfPropertyPlantAndEquipmentInvCF", # 有形固定資産の取得による支出 有形固定資産の取得による支出、投資活動によるキャッシュ・フロー monetaryItemType	12315
    "jppfs_cor:ExtraordinaryIncome", # 特別利益 特別利益 monetaryItemType	12288
    "jppfs_cor:DividendsFromSurplus", # 剰余金の配当 剰余金の配当 monetaryItemType	12232
    "jppfs_cor:DividendsIncomeNOI", # 受取配当金 受取配当金、営業外収益 monetaryItemType	11481
    "jppfs_cor:PurchaseOfTreasuryStock", # 自己株式の取得 自己株式の取得 monetaryItemType	11368
    "jppfs_cor:IncreaseDecreaseInAllowanceForDoubtfulAccountsOpeCF", # 貸倒引当金の増減額（△は減少） 貸倒引当金の増減額（△は減少）、営業活動によるキャッシュ・フロー monetaryItemType	11330
    "jppfs_cor:RepaymentOfLongTermLoansPayableFinCF", # 長期借入金の返済による支出 長期借入金の返済による支出、財務活動によるキャッシュ・フロー monetaryItemType	11171
    "jppfs_cor:RetirementBenefitExpensesSGA", # 退職給付費用 退職給付費用、販売費及び一般管理費 monetaryItemType	11103
    "jppfs_cor:EffectOfExchangeRateChangeOnCashAndCashEquivalents", # 現金及び現金同等物に係る換算差額 現金及び現金同等物に係る換算差額 monetaryItemType	11034
    "jppfs_cor:PurchaseOfInvestmentSecuritiesInvCF", # 投資有価証券の取得による支出 投資有価証券の取得による支出、投資活動によるキャッシュ・フロー monetaryItemType	10293
    "jppfs_cor:IncreaseDecreaseInNetDefinedBenefitLiabilityOpeCF", # 退職給付に係る負債の増減額（△は減少） 退職給付に係る負債の増減額（△は減少）、営業活動によるキャッシュ・フロー monetaryItemType	10117
    "jppfs_cor:PurchaseOfIntangibleAssetsInvCF", # 無形固定資産の取得による支出 無形固定資産の取得による支出、投資活動によるキャッシュ・フロー monetaryItemType	9940
    "jppfs_cor:ProvisionForBonusesSGA", # 賞与引当金繰入額 賞与引当金繰入額、販売費及び一般管理費 monetaryItemType	9815
]

not_used = [
    "jppfs_cor:InterestExpensesNOE", # 支払利息 支払利息、営業外費用 monetaryItemType	13528
    "jppfs_cor:InterestExpensesOpeCF", # 支払利息 支払利息、営業活動によるキャッシュ・フロー monetaryItemType	12835

    "jppfs_cor:OtherNOI", # その他 その他、営業外収益 monetaryItemType	12255
    "jppfs_cor:OtherNOE", # その他 その他、営業外費用 monetaryItemType	12012
    "jppfs_cor:OtherNetOpeCF", # その他 その他、営業活動によるキャッシュ・フロー monetaryItemType	12886
    "jppfs_cor:OtherNetInvCF", # その他 その他、投資活動によるキャッシュ・フロー monetaryItemType	11160

]

account_dic = {}

def print_freq(vcnt, top):
    v = list(sorted(vcnt.items(), key=lambda x:x[1], reverse=True))
    for w, cnt in v[:top]:
        print(w, cnt)

def print_context_freq(log_f, vcnt):
    for idx, context_ref in enumerate(context_refs):
        if len(vcnt[idx]) == 0:
            continue

        log_f.write("context:\t%s\n" % context_ref)
        v = list(sorted(vcnt[idx].items(), key=lambda x:x[1], reverse=True))
        for w, cnt in v[:200]:
            log_f.write("%s\t%d\n" % (w, cnt))
        log_f.write("\n")

    log_f.write("\n")

def getDocList(day_path: str, url: str):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = json.load(res)

    assert body['metadata']['message'] == "OK"

    # JSONをファイルに書く。
    json_path = "%s/docs.json" % day_path
    with codecs.open(json_path, 'w', 'utf-8') as json_f:
        json.dump(body, json_f, ensure_ascii=False)

    return body

def download_file(url, dst_path):
    with urllib.request.urlopen(url) as web_file:
        data = web_file.read()
        with open(dst_path, mode='wb') as local_file:
            local_file.write(data)

    # try:
    # except urllib.error.URLError as e:
    #     print(e)

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
report_path = root_dir + '/web/report'

data_path = root_dir + '/python/data'
docs_path = root_dir + '/xbrl-zip'

for path in [data_path, docs_path]:
    if not os.path.exists(path):
        # フォルダーがなければ作る。

        os.makedirs(path)

ns_xsd_dic = {}
company_dic = read_company_dic()

class Account:
    label: str
    verboseLabel: str
    elementName: str
    type: str
    depth: int

    def __init__(self, items):
        self.label = items[1]
        self.verboseLabel = items[2]
        self.elementName = items[8]
        self.type = items[9]
        self.depth = int(items[14])



def readAccounts():
    path = '%s/data/EDINET/勘定科目リスト.csv' % root_dir
    lines = read_lines(path)
    
    accounts = {}

    lines = lines[2:]
    for line in lines:
        items = line.split('\t')

        # 0:科目分類 1:標準ラベル（日本語） 2:冗長ラベル（日本語） 3:標準ラベル（英語） 4:冗長ラベル（英語） 5:用途区分、財務諸表区分及び業種区分のラベル（日本語） 6:用途区分、財務諸表区分及び業種区分のラベル（英語） 7:名前空間プレフィックス 8:要素名 9:type 10:substitutionGroup 11:periodType 12:balance 13:abstract 14:depth
        if len(items) != 15 or items[7] != 'jppfs_cor':
            continue

        account = Account(items)
        accounts[account.elementName] = account

    return accounts

vv = Counter()
vp = Counter()
label_cnt = Counter()
def read_jppfs_cor(el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)
    if uri.endswith("/jpcrp_cor") or uri.endswith("/jppfs_cor"):

        context_ref = el.get("contextRef")

        if context_ref is not None:

            contexts = context_ref.split('_')
            if contexts[0].startswith("Prior"):
                return

            if uri.endswith("/jpcrp_cor"):
                if not tag_name in verbose_label_dic:
                    return

                label_cnt[verbose_label_dic[tag_name]] += 1

            else:
                if not tag_name in accounts:
                    return

                acc = accounts[tag_name]
                label_cnt[acc.verboseLabel] += 1


            vp[contexts[0]] += 1

            if context_ref in vv:
                    vv[context_ref] += 1
            else:
                if len(vv) < 100 * 10000:
                    vv[context_ref] += 1

                    if len(vv) % 10000 == 0:

                        print("------------------------------------------------------------------------------------------\n")
                        for w, cnt in sorted(vp.items(), key=lambda x:x[1], reverse=True):
                            print(w, cnt)

                        print("------------------------------ context \n")
                        v2 = sorted(vv.items(), key=lambda x:x[1], reverse=True)
                        for ctx, cnt in v2[:100]:
                            print(ctx, cnt)

                        print("------------------------------ label \n")
                        v2 = sorted(label_cnt.items(), key=lambda x:x[1], reverse=True)
                        for name, cnt in v2[:100]:
                            print(name, cnt)

            return



    # 再帰的にXBRLファイルの内容を読む。
    for child in el:
        read_jppfs_cor(child)

def get_xbrl_zip_bin():
    xbrl = re.compile('XBRL/PublicDoc/jpcrp[-_0-9a-zA-Z]+\.xbrl')
    for zip_path_obj in Path(docs_path).glob("**/*.zip"):
        zip_path = str(zip_path_obj)

        try:
            with zipfile.ZipFile(zip_path) as zf:
                xbrl_file = find(x for x in zf.namelist() if xbrl.match(x))
                if xbrl_file is None:
                    # print("no xbrl", zip_path)
                    continue

                with zf.open(xbrl_file) as f:
                    xml_bin = f.read()
        except zipfile.BadZipFile:
            print("\nBadZipFile : %s\n" % zip_path)
            continue
                
        xbrl_file_name = xbrl_file.split('/')[-1]
        yield xbrl_file_name, xml_bin

def get_xbrl_zip_root():
    for xbrl_file_name, xml_bin in get_xbrl_zip_bin():
        xml_text = xml_bin.decode('utf-8')
        root = ET.fromstring(xml_text)

        yield xbrl_file_name, root

def get_xbrl_root():
    dir_path = "%s/xbrl-xml" % root_dir
    for xml_path_obj in Path(dir_path).glob("**/*.xbrl"):
        xml_path = str(xml_path_obj)
        xbrl_file_name = xml_path.split(os.sep)[-1]
        root = ET.parse(xml_path).getroot()

        yield xbrl_file_name, root

                

def check_zip_file(zip_path: str):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            file_list = list(zf.namelist())

        return True
    except zipfile.BadZipFile:
        return False

def download_docs(yyyymmdd, day_path, body, retry):
    for doc in body['results']:   
        docTypeCode = doc['docTypeCode']
        if docTypeCode in [ '120', '130', '140', '150', '160', '170' ]:
            edinetCode = doc['edinetCode']
            if edinetCode in company_dic:
                company = company_dic[edinetCode]
                if company['listing'] == '上場':

                    dst_path = "%s/%s-%s.zip" % (day_path, edinetCode, docTypeCode)

                    if os.path.exists(dst_path) and check_zip_file(dst_path):
                        continue

                    print("%s | %s | %s | %s | %s" % (yyyymmdd, doc['filerName'], doc['docDescription'], company['listing'], company['category_name']))

                    url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/%s?type=1" % doc['docID']
                    download_file(url, dst_path)

                    if not check_zip_file(dst_path):
                        print("!!!!!!!!!! ERROR !!!!!!!!!!\n" * 10)
                        time.sleep(10)

                    time.sleep(1)

def get_xbrl_docs():
    dt1 = None
    
    while True:
        if dt1 is None:
            dt1 = datetime.datetime(year=2018, month=8, day=10)
        else:
            dt1 = dt1 + datetime.timedelta(days=-1)
            
        yyyymmdd = "%d-%02d-%02d" % (dt1.year, dt1.month, dt1.day)
        print(yyyymmdd)

        day_path = "%s/%d/%02d/%02d" % (docs_path, dt1.year, dt1.month, dt1.day)
        if not os.path.exists(day_path):
            # フォルダーがなければ作る。

            os.makedirs(day_path)

        os.chdir(day_path)

        url = 'https://disclosure.edinet-fsa.go.jp/api/v1/documents.json?date=%s&type=2' % yyyymmdd
        body = getDocList(day_path, url)
        time.sleep(1)

        download_docs(yyyymmdd, day_path, body, False)

def retry_get_xbrl_docs():
    for json_path_obj in Path(docs_path).glob("**/docs.json"):
        json_path = str(json_path_obj)

        paths = json_path.split(os.sep)
        yyyymmdd = "%s-%s-%s" % (paths[-4], paths[-3], paths[-2])
        day_path = "%s/%s/%s/%s" % (docs_path, paths[-4], paths[-3], paths[-2])

        with codecs.open(json_path, 'r', 'utf-8') as f:
            body = json.load(f)

        download_docs(yyyymmdd, day_path, body, True)

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
            v = [x for x in xsd_dic.items() if len(x[1].calcTo) != 0]
            for ele in OrderedDict.fromkeys(xsd_dic.values()).keys():
                if len(ele.calcTo) != 0:
                    log_f.write(ele.verbose_label + '\n')
                    for calc in ele.calcTo:
                        log_f.write("\t%s %f %s %s\n" % (calc.to.verbose_label, calc.order, calc.weight, calc.role))




        ns_xsd_dic[prefix] = xsd_dic

    # assert xsd_dics[uri] == xsd_dic


def read_jpcrp_labelArc(el: ET.Element, labelArcs):
    id, uri, tag_name, text = parseElement(el)

    if tag_name == "labelArc":
        attr = getAttribs(el)

        assert 'from' in attr and 'to' in attr
        labelArcs[attr['to']] = attr['from']

    for child in el:
        read_jpcrp_labelArc(child, labelArcs)


def read_jpcrp_label(el: ET.Element, labelArcs, label_dic, verbose_label_dic):
    id, uri, tag_name, text = parseElement(el)


    if tag_name == "label":

        attr = getAttribs(el)
        assert 'label' in attr and 'role' in attr
        assert attr['label'] in labelArcs
        label = labelArcs[attr['label']]

        if attr['role'] == label_role:
            label_dic[label] = el.text
        elif attr['role'] == verboseLabel_role:
            verbose_label_dic[label] = el.text

    # 再帰的にXBRLファイルの内容を読む。
    for child in el:
        read_jpcrp_label(child, labelArcs, label_dic, verbose_label_dic)

def read_label():
    label_path = "%s/data/EDINET/taxonomy/2019-11-01/taxonomy/jpcrp/2019-11-01/label/jpcrp_2019-11-01_lab.xml" % root_dir
    root = ET.parse(label_path).getroot()
    labelArcs = {}
    read_jpcrp_labelArc(root, labelArcs)

    label_dic = {}
    verbose_label_dic = {}
    read_jpcrp_label(root, labelArcs, label_dic, verbose_label_dic)

    return label_dic, verbose_label_dic

def extract_xbrl():
    cnt = 0
    for xbrl_file, xml_bin in get_xbrl_zip_bin():
        v1 = xbrl_file.split('_')
        v2 = v1[1].split('-')
        edinetCode = v2[0]
        if edinetCode in company_dic:
            category_name = company_dic[edinetCode]["category_name"]
        else:
            category_name = "other"

        dir_path = "%s/xbrl-xml/%s/%s" % (root_dir, category_name, edinetCode)
        if not os.path.exists(dir_path):
            # フォルダーがなければ作る。

            os.makedirs(dir_path)

        xml_path = dir_path + "/" + xbrl_file
        with open(xml_path, "wb") as f:
            f.write(xml_bin)

        cnt += 1
        if cnt % 100 == 0:
            print(cnt)

    print("合計 : %d" % cnt)

context_refs = [ "FilingDateInstant", "CurrentYearInstant", "CurrentYearInstant_NonConsolidatedMember", "CurrentYearDuration", "CurrentYearDuration_NonConsolidatedMember", "CurrentQuarterInstant", "CurrentQuarterInstant_NonConsolidatedMember", "CurrentYTDDuration", "CurrentYTDDuration_NonConsolidatedMember", "InterimInstant", "InterimInstant_NonConsolidatedMember", "InterimDuration", "InterimDuration_NonConsolidatedMember"  ]
CurrentPeriodEndDate_dic = {}

def xbrl_test(edinetCode, values, vloc, vcnt, vifrs, vusgaap, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)        

    if tag_name == "xbrl":
        for child in el:
            xbrl_test(edinetCode, values, vloc, vcnt, vifrs, vusgaap, child)
        return

    if text is None:
        return

    context_ref = el.get("contextRef")
    if context_ref is None or not context_ref in context_refs: # context_ref.startswith("Prior"):
        return

    idx = context_refs.index(context_ref)

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
    if id in account_dic:
        values[account_dic[id]] = text
        # 報告書インスタンス 作成ガイドライン
        #   5-6-2 数値を表現する要素
        
        if id == "jpdei_cor:CurrentPeriodEndDateDEI":
            key = edinetCode + '\t' + text
            if key in CurrentPeriodEndDate_dic:

                print("当会計期間終了日 %s %s" % (edinetCode, text))
            else:
                CurrentPeriodEndDate_dic[key] = text


    
    name = '"%s:%s", # %s %s %s' % (ns, tag_name, ele.label, ele.verbose_label, ele.type)
    # name = context_ref

    vloc[idx][name] += 1

    if "IFRS" in tag_name:
        vifrs[idx][name] += 1
    elif "USGAAP" in tag_name:
        vusgaap[idx][name] += 1
    else:
        vcnt[idx][name] += 1



def xbrl_test2(vloc, vcnt, vifrs, vusgaap, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)

    if tag_name == "xbrl":
        # for child in el:
        #     xbrl_test(vloc, vcnt, vifrs, vusgaap, child)
        return

    context_ref = el.get("contextRef")
    if context_ref is None or context_ref.startswith("Prior"):
        return

    ns = uri.split('/')[-1]

    jp = ""
    
    if uri.endswith("/jppfs_cor"):
        if tag_name in accounts:
            jp = ":" + accounts[tag_name].verboseLabel
    elif uri.endswith("/jpcrp_cor"):
        if tag_name in verbose_label_dic:
            jp = ":" + verbose_label_dic[tag_name]

    name = "%s:%s:%s%s" % (context_ref, ns, tag_name, jp)
    # name = context_ref

    vloc[name] += 1

    if "IFRS" in tag_name:
        vifrs[name] += 1
    elif "USGAAP" in tag_name:
        vusgaap[name] += 1
    else:
        vcnt[name] += 1

    # if context_ref in [ "CurrentYearInstant", "CurrentQuarterInstant", "InterimInstant", "CurrentYTDDuration", "CurrentYearDuration" ]:
    # if tag_name in ["NetSales", "OperatingIncome", "OperatingRevenue1", "OperatingRevenue2"]: # "Assets":

def xbrl_test_ifrs(vcnt, el: ET.Element):
    """XBRLファイルの内容を読む。
    """
    id, uri, tag_name, text = parseElement(el)
    if "IFRS" in tag_name:

        context_ref = el.get("contextRef")

        if context_ref is not None and not context_ref.startswith("Prior"):

            uri.split('/')[-1]
            if tag_name in verbose_label_dic:
                jp = ":" + verbose_label_dic[tag_name]
            else:
                jp = ""
            vcnt[uri.split('/')[-1] + ":" + tag_name + jp] += 1
            return

    for child in el:
        xbrl_test_ifrs(vcnt, child)

def test_main():
    with codecs.open(data_path + "/schema.txt", 'w', 'utf-8') as log_f:
        ReadAllSchema(log_f)

    csv_f = codecs.open(data_path + "/report.csv", 'w', 'utf-8')

    titles = []
    for i, id in enumerate(account_ids):
        assert not id in account_dic
        account_dic[id] = i

        ns, tag_name = id.split(':')

        assert ns in ns_xsd_dic
        xsd_dic = ns_xsd_dic[ns]
        assert tag_name in xsd_dic
        ele =xsd_dic[tag_name]

        assert not "," in ele.label
        assert not ele.label in titles
        titles.append(ele.label)

    csv_f.write("%s\n" % ",".join(titles) )




    label_dic, verbose_label_dic = read_label()
    accounts = readAccounts()
    vcnt1 = [ Counter() for _ in context_refs ]
    vcnt2 = [ Counter() for _ in context_refs ]
    vcnt3 = [ Counter() for _ in context_refs ]
    vifrs = [ Counter() for _ in context_refs ]
    vusgaap = [ Counter() for _ in context_refs ]

    cnt = 0
    for xbrl_file_name, root in get_xbrl_zip_root():
        v1 = xbrl_file_name.split('_')
        if v1[3] != "01":
            # 訂正の場合

            continue

        edinetCode = v1[1].split('-')[0]
        if not edinetCode in company_dic:
            continue
        company = company_dic[edinetCode]
        if company['category_name_jp'] in ["保険業", "その他金融業", "証券、商品先物取引業", "銀行業"]:
            continue

        v2 = v1[0].split('-')
        repo = v2[1]
        if repo == "asr":
            vcnt = vcnt1
        elif repo in [ "q1r", "q2r", "q3r", "q4r" ]:
            vcnt = vcnt2
        elif repo == "ssr":
            vcnt = vcnt3
        else:
            assert False

        vloc  = [ Counter() for _ in context_refs ]
        values = [""] * len(account_ids)
        xbrl_test(edinetCode, values, vloc, vcnt, vifrs, vusgaap, root)
        csv_f.write("%s\n" % ",".join(values) )

        if sum(len(x) for x in vloc) == 0:
            print(xbrl_file_name, company['category_name_jp'])

        cnt += 1
        if cnt % 1000 == 0:
            print(cnt)
            with codecs.open(data_path + "/log.txt", 'w', 'utf-8') as log_f:
                for txt, v in [ [reports[0], vcnt1], [reports[1], vcnt2], [reports[2], vcnt3], [reports[3], vifrs], [reports[4], vusgaap] ]:
                    log_f.write("report:\t%s\n" % txt)
                    print_context_freq(log_f, v)
                    log_f.write("\n")

    csv_f.close()
    print("合計:%d" % cnt)

if __name__ == '__main__':

    args = sys.argv
    if len(args) == 2:
        if args[1] == "get":
            get_xbrl_docs()

        elif args[1] == "jppfs":
            accounts = readAccounts()
            label_dic, verbose_label_dic = read_label()
            for xbrl_file, root in get_xbrl_zip_root():
                read_jppfs_cor(root)

        elif args[1] == "retry":
            retry_get_xbrl_docs()

        elif args[1] == "test":
            test_main()

        elif args[1] == "extract":
            extract_xbrl()

        elif args[1] == "time":
            start_time = time.time()
            cnt = 0

            # for xbrl_file_name, root in get_xbrl_zip_root():


                # cnt += 1
                # if cnt % 100 == 0:
                #     print(cnt, int(time.time() - start_time) / cnt)
