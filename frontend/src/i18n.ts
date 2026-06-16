// MarketMind AI Dashboard - Internationalization (EN / TH)
export type Language = "en" | "th";

const translations: Record<Language, Record<string, string>> = {
  en: {
    appTitle: "MarketMind AI",
    appSubtitle: "Research Console",
    searchPlaceholder: "Enter stock symbol (e.g. AAPL, TSLA)...",
    analyzeBtn: "Analyze",
    analyzingBtn: "Analyzing...",
    loadingMessage: "Analyzing {symbol}... AI agents are researching, analyzing sentiment, debating, and generating insights.",
    loadingSubtext: "This may take 1-2 minutes while AI agents analyze the data",
    emptyTitle: "MarketMind AI Dashboard",
    emptyDesc: "Enter a stock symbol above to start an AI-powered analysis. Our multi-agent system will research news, analyze sentiment, debate bull vs bear cases, and deliver a final investment recommendation.",
    emptyHint: "Try: AAPL, TSLA, MSFT, GOOGL, AMZN, NVDA, META",
    homeEyebrow: "AI investment brief",
    homeTitle: "AI Investment Brief for any stock",
    homeSubtitle: "Enter a ticker and get a concise final call, bull and bear evidence, risk, valuation, and source quality in one readable brief.",
    homeSearchLabel: "Start with a stock symbol",
    homeTickerLabel: "Suggested tickers",
    homeFeatureDecision: "Final call",
    homeFeatureDebate: "Bull/Bear debate",
    homeFeatureSources: "Source quality",
    homePreviewSymbol: "Brief preview",
    homePreviewStatus: "Example",
    homePreviewAction: "Final call",
    homePreviewEvidence: "Evidence",
    homePreviewAppendix: "Appendix",
    homePreviewReason: "A clean one-page brief with the final view first, then the reasoning and supporting detail.",
    homePreviewStepResearch: "Collect market data",
    homePreviewStepDebate: "Compare bull vs bear",
    homePreviewStepBrief: "Write the brief",
    homePreviewMetricDecision: "Decision",
    homePreviewMetricDecisionValue: "Buy / Hold / Sell",
    homePreviewMetricRisk: "Risk",
    homePreviewMetricRiskValue: "Macro / Company",
    homePreviewMetricSources: "Sources",
    homePreviewReady: "Ready",
    errorPrefix: "Error:",
    tryAgain: "Try Again",
    cachedWarning: "⚠ Cached data",
    partialAnalysis: "Partial analysis",
    warningsTitle: "⚠️ Analysis Warnings",

    // Dashboard cards
    sentimentTitle: "Market Sentiment",
    cioTitle: "CIO Final Decision",
    bullBearTitle: "Bull vs Bear Thesis",
    bullCase: "Bull Case",
    bearCase: "Bear Case",
    noBullThesis: "No bull thesis generated",
    noBearThesis: "No bear thesis generated",
    confidence: "Confidence",
    risk: "Risk",
    horizon: "Horizon",

    riskTitle: "Risk Assessment",
    macroRisk: "Macro",
    companyRisk: "Company",
    volatilityRisk: "Volatility",

    valuationTitle: "Valuation",
    peRatio: "P/E Ratio",
    sectorAvgPE: "Sector Avg P/E",
    pegRatio: "PEG Ratio",
    marketCap: "Market Cap",
    na: "N/A",

    debateTitle: "AI Debate Transcript",
    newsTitle: "News Feed",
    articles: "articles",
    translationMissing: "Thai translation is not available for this section.",

    // Decision Hero
    decisionHeroTitle: "CIO Decision",
    keyPoints: "Key Points",
    noKeyPoints: "No key points available.",
    statusBarStale: "Cached data",
    statusBarPartial: "Partial analysis",
    statusBarMissingThai: "Thai translations: {missing} section(s) incomplete",

    // Metrics Panel
    metricSentiment: "Sentiment",
    metricRisk: "Risk",
    metricValuation: "Valuation",
    riskSummary: "Summary",
    valuationVerdict: "Verdict",

    // Secondary sections
    winner: "Winner",
    secondaryDebate: "AI Debate",
    secondaryNews: "News & Research",

    // Dividers
    detailsSection: "Details & Supporting Analysis",

    // Catalysts
    catalysts: "Catalysts",
    riskFactors: "Risk Factors",
    evidence: "Evidence",

    // Executive Summary
    execSummaryTitle: "Executive Summary",
    execTheCall: "The Call",
    execWhy: "Why It Makes Sense",
    execWhatCouldChange: "What Could Change the View",
    execBullConfidence: "Bull confidence: {pct}%",
    execBearConfidence: "Bear confidence: {pct}%",
    execBullSide: "Bull case",
    execBearSide: "Bear case",
    execRiskLevel: "Overall risk profile: {level}",
    execNotAvailable: "Insufficient data for executive summary.",
    evidenceSection: "Evidence",
    appendixSection: "Appendix & Details",
    sourceQualityTitle: "Source Quality",
    sourceQuality_good: "Good",
    sourceQuality_partial: "Partial",
    sourceQuality_poor: "Poor",
    sourceQuality_unknown: "Unknown",
    sourceNewsCount: "News articles",
    sourceRedditCount: "Reddit posts",
    sourcePrice: "Price source",
    sourceFundamentals: "Fundamentals",
    sourceMacro: "Macro",
    sourceFetchedAt: "Fetched",
    sourceList: "Sources",
    sourceUnknown: "Unknown",

    // Trace panel
    traceTitle: "Agent Trace",
    traceEmpty: "No trace data available. Run an analysis to see agent activity.",
    traceWaiting: "Waiting for agents to start...",

    // Reliability panel
    reliabilityTitle: "Evidence Reliability",
    reliabilityEmpty: "No reliability data available. Run an analysis to compute evidence quality.",
    reliabilityOverall: "Overall Reliability",
    reliabilityDiversity: "Source Diversity",
    reliabilityFreshness: "Data Freshness",
    reliabilityCompleteness: "Completeness",
    reliabilitySources: "Unique Sources",
    reliabilityItems: "Evidence Items",
    reliabilityQuality: "Data Quality",

    // Memo panel
    memoPanelTitle: "Investment Memo",
    noMemoAvailable: "No investment memo available. Run an analysis to generate a citation-grounded research memo.",
    executiveSummary: "Executive Summary",
    recommendation: "Recommendation",
    keyCitations: "Key Citations",

    // Evidence explorer
    evidenceExplorerTitle: "Evidence Explorer",
    noEvidenceAvailable: "No evidence items available. Evidence is built from research data and agent outputs.",

    // Grounding panel
    groundingPanelTitle: "Citation Grounding",
    noGroundingAvailable: "No grounding report available. A grounding report is generated alongside the investment memo.",
    groundingScore: "Grounding Score",
    groundingClaimCount: "Claims",
    groundingCitedClaims: "Cited Claims",
    groundingValidCitations: "Valid Citations",
    groundingInvalidCitations: "Invalid Citations",
    groundingIssues: "Issues",
    groundingIssueMissingCitation: "Missing Citation",
    groundingIssueUnknownEvidenceId: "Unknown Evidence ID",
    groundingIssueWeakOverlap: "Weak Overlap",

    // Evidence explorer
    evidenceFilterAll: "All",
    evidenceFilterNews: "News",
    evidenceFilterReddit: "Reddit",
    evidenceFilterCompany: "Company",
    evidenceFilterFundamentals: "Fundamentals",
    evidenceFilterMacro: "Macro",
    evidenceFilterAgent: "Agent",
    evidenceSearchPlaceholder: "Search evidence...",
    evidenceNoMatches: "No evidence matches your filters.",

    // Agent trace panel
    traceAgentResearch: "Research",
    traceAgentSentiment: "Sentiment",
    traceAgentValuation: "Valuation",
    traceAgentBullCase: "Bull Case",
    traceAgentBearCase: "Bear Case",
    traceAgentRisk: "Risk",
    traceAgentDebate: "Debate",
    traceAgentCIO: "CIO Decision",
    traceAgentMemo: "Investment Memo",
    traceStatusPending: "pending",
    traceStatusRunning: "running",
    traceStatusComplete: "complete",
    traceStatusFailed: "failed",
    traceToolCalls: "Tool Calls",
    traceTools: "tools",

    // Memo section headings
    memoHeadingDecisionRationale: "Decision Rationale",
    memoHeadingBullCase: "Bull Case",
    memoHeadingBearCase: "Bear Case",
    memoHeadingKeyRisks: "Key Risks",
    memoHeadingWhatWouldChangeView: "What Would Change the View",
    memoTitlePrefix: "Investment Research Memo: ",

    // Comparison mode
    compareMode: "Compare Stocks",
    singleMode: "Single Analysis",
    singleModeDesc: "Deep-dive one stock",
    compareModeDesc: "Compare 2–4 stocks side-by-side",
    comparePlaceholder: "Add 2-4 symbols (e.g. AAPL, MSFT, GOOGL)",
    compareBtn: "Compare",
    comparingBtn: "Comparing...",
    compareLoading: "Analyzing symbols... AI agents are working in parallel.",
    winnerCard: "Winner",
    comparisonTable: "Comparison Table",
    rankingRationale: "Ranking Rationale",
    noCompareResult: "No comparison results yet. Enter 2-4 stock symbols above to start a comparison.",

    // Evaluation panel
    evaluationTitle: "AI Quality Evaluation",
    evaluationNoData: "No evaluation metrics available. Run and complete an analysis first.",
    evalOverall: "Overall Quality",
    evalCitationValidity: "Citation Validity",
    evalGrounding: "Grounding Score",
    evalEvidenceCount: "Evidence Count",
    evalSourceDiversity: "Source Diversity",
    evalAgentCompletion: "Agent Completion",
    evalMemoCompleteness: "Memo Completeness",
    evalMissingFields: "Missing Fields",
    evalWarnings: "Warnings",

    // Export
    exportMemo: "Export Markdown",
    exportingMemo: "Exporting...",
    exportError: "Failed to export memo",

    // Comparison panel (additional labels)
    compareNewComparison: "New Comparison",
    compareTimedOut: "Comparison timed out",
    compareStillRunning: "Comparison may still be running on the server.",
    compareCheckAgain: "Check result again",
    compareAddBtn: "Add",
    compareErrorsTitle: "Comparison Errors",
    compareRiskLabel: "Risk",
    compareSentimentLabel: "Sentiment",
    compareReliabilityLabel: "Reliability",
    compareGroundingLabel: "Grounding",
    compareBullPoints: "Bull Points",
    compareBearPoints: "Bear Points",
    compareValuation: "Valuation",
    compareProgressLabel: "Progress",
    compareTimeoutMessage: "Polling timed out after 5 minutes. The backend may still be processing.",

    // Evaluation panel (additional labels)
    evalLoadingMetrics: "Loading evaluation metrics...",

    // Comparison table headers
    compareTableSymbol: "Symbol",
    compareTableAction: "Action",
    compareTableConfidence: "Confidence",

    // Comparison empty state
    compareEmptyTitle: "Compare Stocks",
    compareEmptyDesc: "Run side-by-side AI analysis on 2–4 stocks to compare CIO decisions, risk, sentiment, reliability, and grounding scores. The system ranks the strongest pick automatically.",
    compareEmptyHint: "Enter symbols above (e.g., AAPL, MSFT) or paste comma-separated (AAPL, MSFT, GOOGL)",

    // Comparison progress
    compareProgressOf: "{done} of {total} symbols complete",

    // Demo
    demoLoadBtn: "Load Demo",
  },

  th: {
    appTitle: "MarketMind AI",
    appSubtitle: "Research Console",
    searchPlaceholder: "ป้อนสัญลักษณ์หุ้น (เช่น AAPL, TSLA)...",
    analyzeBtn: "วิเคราะห์",
    analyzingBtn: "กำลังวิเคราะห์...",
    loadingMessage: "กำลังวิเคราะห์ {symbol}... AI agents กำลังค้นคว้าข่าว วิเคราะห์อารมณ์ตลาด ถกเถียง และสร้างข้อมูลเชิงลึก",
    loadingSubtext: "อาจใช้เวลา 1-2 นาทีระหว่างที่ AI agents วิเคราะห์ข้อมูล",
    emptyTitle: "MarketMind AI Dashboard",
    emptyDesc: "ป้อนสัญลักษณ์หุ้นด้านบนเพื่อเริ่มการวิเคราะห์ด้วย AI ระบบ multi-agent ของเราจะค้นคว้าข่าว วิเคราะห์อารมณ์ตลาด ถกเถียงกรณี bull vs bear และให้คำแนะนำการลงทุนขั้นสุดท้าย",
    emptyHint: "ลอง: AAPL, TSLA, MSFT, GOOGL, AMZN, NVDA, META",
    homeEyebrow: "สรุปการลงทุนด้วย AI",
    homeTitle: "Investment Brief สำหรับหุ้นที่คุณสนใจ",
    homeSubtitle: "ป้อนสัญลักษณ์หุ้น แล้วรับคำตัดสินสุดท้าย เหตุผลฝั่ง Bull/Bear ความเสี่ยง มูลค่า และคุณภาพแหล่งข้อมูลในหน้าเดียว",
    homeSearchLabel: "เริ่มจากสัญลักษณ์หุ้น",
    homeTickerLabel: "หุ้นที่แนะนำให้ลอง",
    homeFeatureDecision: "คำตัดสินสุดท้าย",
    homeFeatureDebate: "Bull/Bear debate",
    homeFeatureSources: "คุณภาพแหล่งข้อมูล",
    homePreviewSymbol: "ตัวอย่าง Brief",
    homePreviewStatus: "ตัวอย่าง",
    homePreviewAction: "คำตัดสิน",
    homePreviewEvidence: "เหตุผลประกอบ",
    homePreviewAppendix: "ภาคผนวก",
    homePreviewReason: "สรุปหน้าเดียวที่เริ่มจากมุมมองสุดท้ายก่อน แล้วค่อยตามด้วยเหตุผลและข้อมูลสนับสนุน",
    homePreviewStepResearch: "รวบรวมข้อมูลตลาด",
    homePreviewStepDebate: "เทียบมุมมอง Bull/Bear",
    homePreviewStepBrief: "สรุปเป็น Brief",
    homePreviewMetricDecision: "คำตัดสิน",
    homePreviewMetricDecisionValue: "ซื้อ / ถือ / ขาย",
    homePreviewMetricRisk: "ความเสี่ยง",
    homePreviewMetricRiskValue: "มหภาค / บริษัท",
    homePreviewMetricSources: "แหล่งข้อมูล",
    homePreviewReady: "พร้อม",
    errorPrefix: "ข้อผิดพลาด:",
    tryAgain: "ลองอีกครั้ง",
    cachedWarning: "⚠ ข้อมูลแคช",
    partialAnalysis: "วิเคราะห์ได้บางส่วน",
    warningsTitle: "⚠️ คำเตือนการวิเคราะห์",

    sentimentTitle: "อารมณ์ตลาด",
    cioTitle: "คำตัดสินสุดท้ายจาก CIO",
    bullBearTitle: "Bull vs Bear Thesis",
    bullCase: "กรณี Bull",
    bearCase: "กรณี Bear",
    noBullThesis: "ไม่มีข้อมูลกรณี bull",
    noBearThesis: "ไม่มีข้อมูลกรณี bear",
    confidence: "ความมั่นใจ",
    risk: "ความเสี่ยง",
    horizon: "ระยะเวลา",

    riskTitle: "ประเมินความเสี่ยง",
    macroRisk: "มหภาค",
    companyRisk: "บริษัท",
    volatilityRisk: "ความผันผวน",

    valuationTitle: "มูลค่าหุ้น",
    peRatio: "P/E Ratio",
    sectorAvgPE: "P/E เฉลี่ยกลุ่ม",
    pegRatio: "PEG Ratio",
    marketCap: "มูลค่าตลาด",
    na: "ไม่มีข้อมูล",

    debateTitle: "บันทึกการโต้วาที AI",
    newsTitle: "ฟีดข่าว",
    articles: "บทความ",
    translationMissing: "ยังไม่มีคำแปลภาษาไทยสำหรับส่วนนี้",

    decisionHeroTitle: "คำตัดสิน CIO",
    keyPoints: "ประเด็นสำคัญ",
    noKeyPoints: "ไม่มีประเด็นสำคัญ",
    statusBarStale: "ข้อมูลแคช",
    statusBarPartial: "วิเคราะห์บางส่วน",
    statusBarMissingThai: "คำแปลภาษาไทย: ขาด {missing} ส่วน",

    metricSentiment: "อารมณ์ตลาด",
    metricRisk: "ความเสี่ยง",
    metricValuation: "มูลค่าหุ้น",
    riskSummary: "สรุป",
    valuationVerdict: "คำตัดสิน",

    winner: "ผู้ชนะ",
    secondaryDebate: "การโต้วาที AI",
    secondaryNews: "ข่าวและการวิจัย",

    detailsSection: "รายละเอียดและการวิเคราะห์สนับสนุน",

    catalysts: "ปัจจัยหนุน",
    riskFactors: "ปัจจัยเสี่ยง",
    evidence: "หลักฐาน",

    execSummaryTitle: "สรุปผู้บริหาร",
    execTheCall: "คำตัดสิน",
    execWhy: "เหตุผลที่สนับสนุน",
    execWhatCouldChange: "ปัจจัยที่อาจเปลี่ยนมุมมอง",
    execBullConfidence: "ความเชื่อมั่นฝั่ง Bull: {pct}%",
    execBearConfidence: "ความเชื่อมั่นฝั่ง Bear: {pct}%",
    execBullSide: "กรณี Bull",
    execBearSide: "กรณี Bear",
    execRiskLevel: "ระดับความเสี่ยงโดยรวม: {level}",
    execNotAvailable: "ข้อมูลไม่เพียงพอสำหรับสรุปผู้บริหาร",
    evidenceSection: "หลักฐาน",
    appendixSection: "ภาคผนวกและรายละเอียด",
    sourceQualityTitle: "คุณภาพแหล่งข้อมูล",
    sourceQuality_good: "ดี",
    sourceQuality_partial: "บางส่วน",
    sourceQuality_poor: "ต่ำ",
    sourceQuality_unknown: "ไม่ทราบ",
    sourceNewsCount: "จำนวนข่าว",
    sourceRedditCount: "โพสต์ Reddit",
    sourcePrice: "แหล่งข้อมูลราคา",
    sourceFundamentals: "ข้อมูลพื้นฐาน",
    sourceMacro: "มหภาค",
    sourceFetchedAt: "ดึงข้อมูลเมื่อ",
    sourceList: "แหล่งข้อมูล",
    sourceUnknown: "ไม่ทราบ",

    // Trace panel
    traceTitle: "Agent Trace",
    traceEmpty: "ไม่มีข้อมูล trace กรุณาวิเคราะห์หุ้นเพื่อดูการทำงานของ agent",
    traceWaiting: "รอให้ agents เริ่มทำงาน...",

    // Reliability panel
    reliabilityTitle: "ความน่าเชื่อถือของหลักฐาน",
    reliabilityEmpty: "ไม่มีข้อมูลความน่าเชื่อถือ กรุณาวิเคราะห์หุ้นเพื่อคำนวณคุณภาพหลักฐาน",
    reliabilityOverall: "ความน่าเชื่อถือโดยรวม",
    reliabilityDiversity: "ความหลากหลายของแหล่งข้อมูล",
    reliabilityFreshness: "ความใหม่ของข้อมูล",
    reliabilityCompleteness: "ความครบถ้วน",
    reliabilitySources: "แหล่งข้อมูล",
    reliabilityItems: "รายการหลักฐาน",
    reliabilityQuality: "คุณภาพข้อมูล",

    // Memo panel
    memoPanelTitle: "บันทึกการลงทุน",
    noMemoAvailable: "ไม่มีบันทึกการลงทุน กรุณาวิเคราะห์หุ้นเพื่อสร้างบันทึกวิจัยที่มีการอ้างอิง",
    executiveSummary: "สรุปผู้บริหาร",
    recommendation: "คำแนะนำ",
    keyCitations: "การอ้างอิงสำคัญ",

    // Evidence explorer
    evidenceExplorerTitle: "คลังหลักฐาน",
    noEvidenceAvailable: "ไม่มีรายการหลักฐาน หลักฐานสร้างจากข้อมูลวิจัยและผลลัพธ์ของ agent",

    // Grounding panel
    groundingPanelTitle: "การตรวจสอบการอ้างอิง",
    noGroundingAvailable: "ไม่มีรายงานการตรวจสอบการอ้างอิง รายงานนี้สร้างพร้อมกับบันทึกการลงทุน",
    groundingScore: "คะแนนการอ้างอิง",
    groundingClaimCount: "จำนวนข้อกล่าวอ้าง",
    groundingCitedClaims: "ข้อกล่าวอ้างที่มีการอ้างอิง",
    groundingValidCitations: "การอ้างอิงที่ถูกต้อง",
    groundingInvalidCitations: "การอ้างอิงที่ไม่ถูกต้อง",
    groundingIssues: "ปัญหา",
    groundingIssueMissingCitation: "ไม่มีการอ้างอิง",
    groundingIssueUnknownEvidenceId: "รหัสหลักฐานไม่ถูกต้อง",
    groundingIssueWeakOverlap: "หลักฐานเกี่ยวข้องน้อย",

    // Evidence explorer
    evidenceFilterAll: "ทั้งหมด",
    evidenceFilterNews: "ข่าว",
    evidenceFilterReddit: "Reddit",
    evidenceFilterCompany: "บริษัท",
    evidenceFilterFundamentals: "ปัจจัยพื้นฐาน",
    evidenceFilterMacro: "มหภาค",
    evidenceFilterAgent: "Agent",
    evidenceSearchPlaceholder: "ค้นหาหลักฐาน...",
    evidenceNoMatches: "ไม่พบหลักฐานที่ตรงกับตัวกรอง",

    // Agent trace panel
    traceAgentResearch: "วิจัยข้อมูล",
    traceAgentSentiment: "วิเคราะห์ความรู้สึก",
    traceAgentValuation: "ประเมินมูลค่า",
    traceAgentBullCase: "กรณีเชิงบวก",
    traceAgentBearCase: "กรณีเชิงลบ",
    traceAgentRisk: "ความเสี่ยง",
    traceAgentDebate: "การโต้วาที",
    traceAgentCIO: "คำตัดสิน CIO",
    traceAgentMemo: "บันทึกการลงทุน",
    traceStatusPending: "รอเริ่ม",
    traceStatusRunning: "กำลังทำงาน",
    traceStatusComplete: "เสร็จแล้ว",
    traceStatusFailed: "ล้มเหลว",
    traceToolCalls: "การใช้เครื่องมือ",
    traceTools: "เครื่องมือ",

    // Memo section headings
    memoHeadingDecisionRationale: "เหตุผลของคำแนะนำ",
    memoHeadingBullCase: "กรณีเชิงบวก",
    memoHeadingBearCase: "กรณีเชิงลบ",
    memoHeadingKeyRisks: "ความเสี่ยงสำคัญ",
    memoHeadingWhatWouldChangeView: "ปัจจัยที่อาจเปลี่ยนมุมมอง",
    memoTitlePrefix: "บันทึกการลงทุน: ",

    // Comparison mode
    compareMode: "เปรียบเทียบหุ้น",
    singleMode: "วิเคราะห์เดี่ยว",
    singleModeDesc: "เจาะลึกหุ้นตัวเดียว",
    compareModeDesc: "เปรียบเทียบหุ้น 2–4 ตัว",
    comparePlaceholder: "เพิ่ม 2-4 สัญลักษณ์ (เช่น AAPL, MSFT, GOOGL)",
    compareBtn: "เปรียบเทียบ",
    comparingBtn: "กำลังเปรียบเทียบ...",
    compareLoading: "กำลังวิเคราะห์สัญลักษณ์... AI agents กำลังทำงานแบบขนาน",
    winnerCard: "ผู้ชนะ",
    comparisonTable: "ตารางเปรียบเทียบ",
    rankingRationale: "เหตุผลการจัดอันดับ",
    noCompareResult: "ยังไม่มีผลการเปรียบเทียบ ป้อนสัญลักษณ์หุ้น 2-4 ตัวด้านบนเพื่อเริ่มเปรียบเทียบ",

    // Evaluation panel
    evaluationTitle: "การประเมินคุณภาพ AI",
    evaluationNoData: "ไม่มีข้อมูลการประเมิน เรียกใช้และวิเคราะห์ให้เสร็จก่อน",
    evalOverall: "คุณภาพโดยรวม",
    evalCitationValidity: "ความถูกต้องของการอ้างอิง",
    evalGrounding: "คะแนนการอ้างอิง",
    evalEvidenceCount: "จำนวนหลักฐาน",
    evalSourceDiversity: "ความหลากหลายของแหล่งข้อมูล",
    evalAgentCompletion: "การทำงานของ Agent",
    evalMemoCompleteness: "ความครบถ้วนของบันทึก",
    evalMissingFields: "ฟิลด์ที่ขาด",
    evalWarnings: "คำเตือน",

    // Export
    exportMemo: "ส่งออก Markdown",
    exportingMemo: "กำลังส่งออก...",
    exportError: "ไม่สามารถส่งออกบันทึกได้",

    // Comparison panel (additional labels)
    compareNewComparison: "การเปรียบเทียบใหม่",
    compareTimedOut: "การเปรียบเทียบหมดเวลา",
    compareStillRunning: "การเปรียบเทียบอาจยังทำงานอยู่บนเซิร์ฟเวอร์",
    compareCheckAgain: "ตรวจสอบผลลัพธ์อีกครั้ง",
    compareAddBtn: "เพิ่ม",
    compareErrorsTitle: "ข้อผิดพลาดการเปรียบเทียบ",
    compareRiskLabel: "ความเสี่ยง",
    compareSentimentLabel: "อารมณ์ตลาด",
    compareReliabilityLabel: "ความน่าเชื่อถือ",
    compareGroundingLabel: "การอ้างอิง",
    compareBullPoints: "จุดเด่น",
    compareBearPoints: "จุดด้อย",
    compareValuation: "มูลค่าหุ้น",
    compareProgressLabel: "ความคืบหน้า",
    compareTimeoutMessage: "การตรวจสอบหมดเวลาหลังจาก 5 นาที เซิร์ฟเวอร์อาจยังทำงานอยู่",

    // Evaluation panel (additional labels)
    evalLoadingMetrics: "กำลังโหลดข้อมูลการประเมิน...",

    // Comparison table headers
    compareTableSymbol: "สัญลักษณ์",
    compareTableAction: "คำแนะนำ",
    compareTableConfidence: "ความมั่นใจ",

    // Comparison empty state
    compareEmptyTitle: "เปรียบเทียบหุ้น",
    compareEmptyDesc: "วิเคราะห์ด้วย AI แบบเคียงข้างกันสำหรับหุ้น 2–4 ตัว เปรียบเทียบคำตัดสินของ CIO ความเสี่ยง อารมณ์ตลาด ความน่าเชื่อถือ และคะแนนการอ้างอิง ระบบจะจัดอันดับตัวเลือกที่ดีที่สุดให้อัตโนมัติ",
    compareEmptyHint: "ป้อนสัญลักษณ์ด้านบน (เช่น AAPL, MSFT) หรือวางแบบคั่นด้วยจุลภาค (AAPL, MSFT, GOOGL)",

    // Comparison progress
    compareProgressOf: "เสร็จแล้ว {done} จาก {total} สัญลักษณ์",

    // Demo
    demoLoadBtn: "โหลดตัวอย่าง",
  },
};

let currentLanguage: Language = (localStorage.getItem("lang") as Language) || "en";

export function getLanguage(): Language {
  return currentLanguage;
}

export function setLanguage(lang: Language): void {
  currentLanguage = lang;
  localStorage.setItem("lang", lang);
}

export function t(key: string, replacements?: Record<string, string>): string {
  const dict = translations[currentLanguage];
  let text = dict[key] || translations["en"][key] || key;
  if (replacements) {
    for (const [k, v] of Object.entries(replacements)) {
      text = text.replace(`{${k}}`, v);
    }
  }
  return text;
}

/** Pick Thai version if language is Thai, otherwise English */
export function l<T>(en: T, th: T | undefined): T {
  const hasThai = (value: unknown): boolean => {
    if (typeof value === "string") return /[\u0E00-\u0E7F]/.test(value);
    if (Array.isArray(value)) return value.some((item) => hasThai(item));
    return false;
  };
  const isTranslated = (value: unknown, fallback: unknown): boolean => {
    if (typeof value === "string") return value.trim() !== "" && hasThai(value);
    if (Array.isArray(value)) {
      if (!Array.isArray(fallback)) return hasThai(value);
      return value.length === fallback.length && value.every((item) => hasThai(item));
    }
    return value !== undefined && value !== null;
  };
  const missing = (): T => {
    if (Array.isArray(en)) return [t("translationMissing")] as T;
    return t("translationMissing") as T;
  };

  if (currentLanguage === "th") {
    if (isTranslated(th, en)) return th as T;
    if (hasThai(en)) return en;
    return missing();
  }
  return en;
}

export function hasThaiText(value: unknown): boolean {
  if (typeof value === "string") return /[\u0E00-\u0E7F]/.test(value);
  if (Array.isArray(value)) return value.some((item) => hasThaiText(item));
  return false;
}

export { translations };
export default translations;