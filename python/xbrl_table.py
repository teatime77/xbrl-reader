account_ids = [
    "jpdei_cor:EDINETCodeDEI", # EDINETコード
    "jpdei_cor:SecurityCodeDEI", # 証券コード 証券コード、DEI stringItemType	17129

    "jpcrp_cor:FilingDateCoverPage", # 提出日 提出日、表紙 dateItemType	17139
    "jpcrp_cor:FiscalYearCoverPage", # 事業年度 事業年度、表紙 stringItemType	17176
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

    "jpcrp_cor:NumberOfConsolidatedSubsidiaries", # 連結子会社の数 連結子会社の数 nonNegativeIntegerItemType	13942
    "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults", # １株当たり当期純利益又は当期純損失（△） １株当たり当期純利益又は当期純損失（△）、経営指標等 perShareItemType	14459
    "jpcrp_cor:DilutedEarningsPerShareSummaryOfBusinessResults", # 潜在株式調整後1株当たり当期純利益 潜在株式調整後1株当たり当期純利益、経営指標等 perShareItemType	14350
    "jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults", # １株当たり純資産額 １株当たり純資産額、経営指標等 perShareItemType	14464
    "jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults", # 自己資本比率 自己資本比率、経営指標等 percentItemType	14461
    "jpcrp_cor:PriceEarningsRatioSummaryOfBusinessResults", # 株価収益率 株価収益率、経営指標等 decimalItemType	14458
    "jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults", # 自己資本利益率 自己資本利益率、経営指標等 percentItemType	14460   
    
    "jppfs_cor:Assets",  # 資産 monetaryItemType    22229
    "jppfs_cor:CurrentAssets", # 流動資産 monetaryItemType  14036
    "jppfs_cor:NoncurrentAssets", # 固定資産 monetaryItemType   14036
    "jppfs_cor:PropertyPlantAndEquipment", # 有形固定資産   13965
    "jppfs_cor:IntangibleAssets", # 無形固定資産    13921
    "jppfs_cor:InvestmentsAndOtherAssets", # 投資その他の資産   14033
    "jppfs_cor:Liabilities", # 負債 monetaryItemType    14665
    "jppfs_cor:CurrentLiabilities", # 流動負債  14036
    "jppfs_cor:NoncurrentLiabilities", # 固定負債   13928
    "jppfs_cor:NetAssets", # 純資産 純資産 monetaryItemType	28047
    "jppfs_cor:ShareholdersEquity", # 株主資本  14040
    "jppfs_cor:CapitalStock", # 資本金  14040
    "jppfs_cor:CapitalSurplus", # 資本剰余金    13796
    "jppfs_cor:RetainedEarnings", # 利益剰余金  14040
    "jppfs_cor:TreasuryStock", # 自己株式   13400

    "jppfs_cor:NetSales", # 売上高 売上高 monetaryItemType	21993
    "jppfs_cor:CostOfSales", # 売上原価 売上原価 monetaryItemType	13293
    "jppfs_cor:GrossProfit", # 売上総利益又は売上総損失（△） 売上総利益又は売上総損失（△） monetaryItemType	13431
    "jppfs_cor:SellingGeneralAndAdministrativeExpenses", # 販売費及び一般管理費 販売費及び一般管理費 monetaryItemType	13984
    "jppfs_cor:SalariesAndAllowancesSGA", # 給料及び手当 給料及び手当、販売費及び一般管理費 monetaryItemType	5525
    "jppfs_cor:ResearchAndDevelopmentExpensesSGA", # 研究開発費 研究開発費、販売費及び一般管理費 monetaryItemType	7298
    "jppfs_cor:OperatingIncome", # 営業利益又は営業損失（△） 営業利益又は営業損失（△） monetaryItemType	22619
    "jppfs_cor:NonOperatingIncome", # 営業外収益 営業外収益 monetaryItemType	14005
    "jppfs_cor:NonOperatingExpenses", # 営業外費用 営業外費用 monetaryItemType	13979
    "jppfs_cor:OrdinaryIncome", # 経常利益又は経常損失（△） 経常利益又は経常損失（△） monetaryItemType	14430
    "jppfs_cor:ExtraordinaryIncome", # 特別利益 特別利益 monetaryItemType	12288
    "jppfs_cor:ExtraordinaryLoss", # 特別損失 特別損失 monetaryItemType	13247
    "jppfs_cor:IncomeBeforeIncomeTaxes", # 税引前当期純利益又は税引前当期純損失（△） 税引前当期純利益又は税引前当期純損失（△） monetaryItemType	28029
    "jppfs_cor:IncomeTaxes", # 法人税等 法人税等 monetaryItemType	13986
    "jppfs_cor:ProfitLoss", # 当期純利益又は当期純損失（△） 当期純利益又は当期純損失（△）（平成26年3月28日財規等改正後） monetaryItemType	21112

    "jppfs_cor:NetCashProvidedByUsedInOperatingActivities", # 営業活動によるキャッシュ・フロー 営業活動によるキャッシュ・フロー monetaryItemType	14009
    "jppfs_cor:NetCashProvidedByUsedInInvestmentActivities", # 投資活動によるキャッシュ・フロー 投資活動によるキャッシュ・フロー monetaryItemType	14009
    "jppfs_cor:NetCashProvidedByUsedInFinancingActivities", # 財務活動によるキャッシュ・フロー 財務活動によるキャッシュ・フロー monetaryItemType	14004
    "jppfs_cor:NetIncreaseDecreaseInCashAndCashEquivalents", # 現金及び現金同等物の増減額（△は減少） 現金及び現金同等物の増減額（△は減少） monetaryItemType	14009
    "jpcrp_cor:CashAndCashEquivalentsSummaryOfBusinessResults", # 現金及び現金同等物の残高 現金及び現金同等物の残高、経営指標等 monetaryItemType	14462
]

not_used = [
    "jppfs_cor:ProfitLossAttributableToOwnersOfParent", # 親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△） 親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△） monetaryItemType	21427
    "jppfs_cor:ComprehensiveIncome", # 包括利益 包括利益 monetaryItemType	14009
    "jppfs_cor:SubtotalOpeCF", # 小計 小計、営業活動によるキャッシュ・フロー monetaryItemType	14009
    "jppfs_cor:ComprehensiveIncomeAttributableToOwnersOfTheParent", # 親会社株主に係る包括利益 親会社株主に係る包括利益、包括利益 monetaryItemType	14007
    "jppfs_cor:IncomeTaxesCurrent", # 法人税、住民税及び事業税 法人税、住民税及び事業税 monetaryItemType	14003
    "jppfs_cor:TotalChangesOfItemsDuringThePeriod", # 当期変動額合計 当期変動額合計 monetaryItemType	13980
    "jppfs_cor:ImpairmentLossEL", # 減損損失 減損損失、特別損失 monetaryItemType	13960
    "jppfs_cor:DepreciationAndAmortizationOpeCF", # 減価償却費 減価償却費、営業活動によるキャッシュ・フロー monetaryItemType	13878
    "jppfs_cor:NetChangesOfItemsOtherThanShareholdersEquity", # 株主資本以外の項目の当期変動額（純額） 株主資本以外の項目の当期変動額（純額） monetaryItemType	13843
    "jppfs_cor:IncomeTaxesDeferred", # 法人税等調整額 法人税等調整額 monetaryItemType	13807
    "jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF", # 売上債権の増減額（△は増加） 売上債権の増減額（△は増加）、営業活動によるキャッシュ・フロー monetaryItemType	13755
    "jppfs_cor:OtherComprehensiveIncome", # その他の包括利益 その他の包括利益 monetaryItemType	13649
    "jppfs_cor:InterestAndDividendsIncomeReceivedOpeCFInvCF", # 利息及び配当金の受取額 利息及び配当金の受取額、営業活動によるキャッシュ・フロー又は投資活動によるキャッシュ・フロー monetaryItemType	13555
    "jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTradeOpeCF", # 仕入債務の増減額（△は減少） 仕入債務の増減額（△は減少）、営業活動によるキャッシュ・フロー monetaryItemType	13498
    "jppfs_cor:InterestIncomeNOI", # 受取利息 受取利息、営業外収益 monetaryItemType	13370
    "jppfs_cor:InterestExpensesPaidOpeCFFinCF", # 利息の支払額 利息の支払額、営業活動によるキャッシュ・フロー又は財務活動によるキャッシュ・フロー monetaryItemType	13217
    "jppfs_cor:InterestAndDividendsIncomeOpeCF", # 受取利息及び受取配当金 受取利息及び受取配当金、営業活動によるキャッシュ・フロー monetaryItemType	13105
    "jppfs_cor:DecreaseIncreaseInInventoriesOpeCF", # たな卸資産の増減額（△は増加） たな卸資産の増減額（△は増加）、営業活動によるキャッシュ・フロー monetaryItemType	12852
    "jppfs_cor:ValuationDifferenceOnAvailableForSaleSecuritiesNetOfTaxOCI", # その他有価証券評価差額金 その他有価証券評価差額金（税引後）、その他の包括利益 monetaryItemType	12773
    "jppfs_cor:IncomeTaxesPaidOpeCF", # 法人税等の支払額 法人税等の支払額、営業活動によるキャッシュ・フロー monetaryItemType	12463
    "jppfs_cor:CashDividendsPaidFinCF", # 配当金の支払額 配当金の支払額、財務活動によるキャッシュ・フロー monetaryItemType	12419
    "jppfs_cor:PurchaseOfPropertyPlantAndEquipmentInvCF", # 有形固定資産の取得による支出 有形固定資産の取得による支出、投資活動によるキャッシュ・フロー monetaryItemType	12315
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

    "jppfs_cor:InterestExpensesNOE", # 支払利息 支払利息、営業外費用 monetaryItemType	13528
    "jppfs_cor:InterestExpensesOpeCF", # 支払利息 支払利息、営業活動によるキャッシュ・フロー monetaryItemType	12835

    "jppfs_cor:OtherNOI", # その他 その他、営業外収益 monetaryItemType	12255
    "jppfs_cor:OtherNOE", # その他 その他、営業外費用 monetaryItemType	12012
    "jppfs_cor:OtherNetOpeCF", # その他 その他、営業活動によるキャッシュ・フロー monetaryItemType	12886
    "jppfs_cor:OtherNetInvCF", # その他 その他、投資活動によるキャッシュ・フロー monetaryItemType	11160
]
