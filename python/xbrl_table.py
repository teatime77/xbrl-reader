filing_date_account_ids = [
    # "jpdei_cor:EDINETCodeDEI", # EDINETコード
    # "jpdei_cor:CurrentPeriodEndDateDEI", # 当会計期間終了日 当会計期間終了日、DEI dateItemType
    # "jpdei_cor:TypeOfCurrentPeriodDEI", # 当会計期間の種類 当会計期間の種類、DEI stringItemType

    "jpcrp_cor:FilingDateCoverPage", # 提出日 提出日、表紙 dateItemType
    "jpdei_cor:SecurityCodeDEI", # 証券コード 証券コード、DEI stringItemType
    "jpcrp_cor:FiscalYearCoverPage", # 事業年度 事業年度、表紙 stringItemType
    "jpdei_cor:CurrentFiscalYearStartDateDEI", # 当事業年度開始日 当事業年度開始日、DEI dateItemType
    "jpdei_cor:CurrentFiscalYearEndDateDEI", # 当事業年度終了日 当事業年度終了日、DEI dateItemType
    "jpdei_cor:AccountingStandardsDEI", # 会計基準 会計基準、DEI stringItemType
    "jpdei_cor:WhetherConsolidatedFinancialStatementsArePreparedDEI", # 連結決算の有無 連結決算の有無、DEI booleanItemType
]

instant_account_ids = [
    "jpcrp_cor:NumberOfEmployees", # 従業員数 従業員数 nonNegativeIntegerItemType
    "jpcrp_cor:AverageNumberOfTemporaryWorkers", # 平均臨時雇用人員 平均臨時雇用人員 decimalItemType
    "jpcrp_cor:AverageAgeYearsInformationAboutReportingCompanyInformationAboutEmployees", # 平均年齢（年） 平均年齢（年）、提出会社の状況、従業員の状況 decimalItemType
    "jpcrp_cor:AverageLengthOfServiceYearsInformationAboutReportingCompanyInformationAboutEmployees", # 平均勤続年数（年） 平均勤続年数（年）、提出会社の状況、従業員の状況 decimalItemType
    "jpcrp_cor:AverageAnnualSalaryInformationAboutReportingCompanyInformationAboutEmployees", # 平均年間給与 平均年間給与、提出会社の状況、従業員の状況 monetaryItemType
    "jpcrp_cor:NumberOfSharesHeld", # 所有株式数 所有株式数 sharesItemType
    "jpcrp_cor:ShareholdingRatio", # 発行済株式（自己株式を除く。）の総数に対する所有株式数の割合 発行済株式（自己株式を除く。）の総数に対する所有株式数の割合 percentItemType
    "jpcrp_cor:TotalNumberOfIssuedSharesSummaryOfBusinessResults", # 発行済株式総数 発行済株式総数（普通株式）、経営指標等 sharesItemType
    "jpcrp_cor:NumberOfConsolidatedSubsidiaries", # 連結子会社の数 連結子会社の数 nonNegativeIntegerItemType
    "jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults", # １株当たり純資産額 １株当たり純資産額、経営指標等 perShareItemType
    "jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults", # 自己資本比率 自己資本比率、経営指標等 percentItemType
    "jpcrp_cor:CashAndCashEquivalentsSummaryOfBusinessResults", # 現金及び現金同等物の残高 現金及び現金同等物の残高、経営指標等 monetaryItemType
    
    "jppfs_cor:Assets",  # 資産 monetaryItemType
    "jppfs_cor:CurrentAssets", # 流動資産 monetaryItemType
    "jppfs_cor:NoncurrentAssets", # 固定資産 monetaryItemType
    "jppfs_cor:PropertyPlantAndEquipment", # 有形固定資産
    "jppfs_cor:IntangibleAssets", # 無形固定資産
    "jppfs_cor:InvestmentsAndOtherAssets", # 投資その他の資産
    "jppfs_cor:Liabilities", # 負債 monetaryItemType
    "jppfs_cor:CurrentLiabilities", # 流動負債
    "jppfs_cor:ShortTermLoansPayable", # 短期借入金 | 短期借入金 | monetaryItemType | 10241
    "jppfs_cor:CurrentPortionOfBonds", # 1年内償還予定の社債 | 1年内償還予定の社債 | monetaryItemType | 2184
    "jppfs_cor:CurrentPortionOfLongTermLoansPayable", # 1年内返済予定の長期借入金 | 1年内返済予定の長期借入金 | monetaryItemType | 7056
    "jppfs_cor:NoncurrentLiabilities", # 固定負債
    "jppfs_cor:BondsPayable", # 社債 | 社債 | monetaryItemType | 2980
    "jppfs_cor:LongTermLoansPayable", # 長期借入金 | 長期借入金 | monetaryItemType | 10584
    "jppfs_cor:NetAssets", # 純資産 純資産 monetaryItemType
    "jppfs_cor:ShareholdersEquity", # 株主資本
    "jppfs_cor:CapitalStock", # 資本金
    "jppfs_cor:CapitalSurplus", # 資本剰余金
    "jppfs_cor:RetainedEarnings", # 利益剰余金
    "jppfs_cor:TreasuryStock", # 自己株式
    "jppfs_cor:ValuationAndTranslationAdjustments", # 評価・換算差額等 | 評価・換算差額等 | monetaryItemType | 13564
]

duration_account_ids = [
    "jppfs_cor:NetSales", # 売上高 売上高 monetaryItemType
    "jppfs_cor:CostOfSales", # 売上原価 売上原価 monetaryItemType
    "jppfs_cor:GrossProfit", # 売上総利益又は売上総損失（△） 売上総利益又は売上総損失（△） monetaryItemType
    "jppfs_cor:SellingGeneralAndAdministrativeExpenses", # 販売費及び一般管理費 販売費及び一般管理費 monetaryItemType
    "jppfs_cor:SalariesAndAllowancesSGA", # 給料及び手当 給料及び手当、販売費及び一般管理費 monetaryItemType
    "jppfs_cor:DepreciationSGA", # 減価償却費 減価償却費、販売費及び一般管理費 monetaryItemType
    "jppfs_cor:ResearchAndDevelopmentExpensesSGA", # 研究開発費 研究開発費、販売費及び一般管理費 monetaryItemType
    "jppfs_cor:OperatingIncome", # 営業利益又は営業損失（△） 営業利益又は営業損失（△） monetaryItemType
    "jppfs_cor:NonOperatingIncome", # 営業外収益 営業外収益 monetaryItemType
    "jppfs_cor:NonOperatingExpenses", # 営業外費用 営業外費用 monetaryItemType
    "jppfs_cor:InterestExpensesNOE", # 支払利息 支払利息、営業外費用 monetaryItemType
    "jppfs_cor:OrdinaryIncome", # 経常利益又は経常損失（△） 経常利益又は経常損失（△） monetaryItemType
    "jppfs_cor:ExtraordinaryIncome", # 特別利益 特別利益 monetaryItemType
    "jppfs_cor:ExtraordinaryLoss", # 特別損失 特別損失 monetaryItemType
    "jppfs_cor:IncomeBeforeIncomeTaxes", # 税引前当期純利益又は税引前当期純損失（△） 税引前当期純利益又は税引前当期純損失（△） monetaryItemType
    "jppfs_cor:IncomeTaxes", # 法人税等 法人税等 monetaryItemType
    "jppfs_cor:ProfitLoss", # 当期純利益又は当期純損失（△） 当期純利益又は当期純損失（△）（平成26年3月28日財規等改正後） monetaryItemType
    "jppfs_cor:ProfitLossAttributableToOwnersOfParent", # 親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△） | 親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△） | monetaryItemType | 21683
    "jpcrp_cor:ComprehensiveIncomeSummaryOfBusinessResults", # 包括利益 | 包括利益、経営指標等 | monetaryItemType | 14258
    "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults", # １株当たり当期純利益又は当期純損失（△） １株当たり当期純利益又は当期純損失（△）、経営指標等 perShareItemType
    "jpcrp_cor:DilutedEarningsPerShareSummaryOfBusinessResults", # 潜在株式調整後1株当たり当期純利益 潜在株式調整後1株当たり当期純利益、経営指標等 perShareItemType
    "jpcrp_cor:DividendPaidPerShareSummaryOfBusinessResults", # １株当たり配当額 １株当たり配当額、経営指標等 perShareItemType
    "jpcrp_cor:PriceEarningsRatioSummaryOfBusinessResults", # 株価収益率 株価収益率、経営指標等 decimalItemType
    "jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults", # 自己資本利益率 自己資本利益率、経営指標等 percentItemType	14460   

    "jppfs_cor:NetCashProvidedByUsedInOperatingActivities", # 営業活動によるキャッシュ・フロー 営業活動によるキャッシュ・フロー monetaryItemType
    "jppfs_cor:DepreciationAndAmortizationOpeCF", # 減価償却費 減価償却費、営業活動によるキャッシュ・フロー monetaryItemType
    "jppfs_cor:NetCashProvidedByUsedInInvestmentActivities", # 投資活動によるキャッシュ・フロー 投資活動によるキャッシュ・フロー monetaryItemType
    "jppfs_cor:NetCashProvidedByUsedInFinancingActivities", # 財務活動によるキャッシュ・フロー 財務活動によるキャッシュ・フロー monetaryItemType
    "jppfs_cor:NetIncreaseDecreaseInCashAndCashEquivalents", # 現金及び現金同等物の増減額（△は減少） 現金及び現金同等物の増減額（△は減少） monetaryItemType
]

all_account_ids = [ filing_date_account_ids, instant_account_ids, duration_account_ids ]
