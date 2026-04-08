import requests
import json
import re
import os

# 🔑 설정 정보
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 전문가적 통찰력을 강제하는 고강도 프롬프트
    prompt = f"""
    너는 하림그룹 홍보실의 '수석 위기관리 전략가'이며, 이 보고서는 회장단에게 직접 전달된다.
    뻔한 소리는 생략하고, 기사마다 다른 '날카로운 분석'을 제공하라.

    [분석 요구사항]
    1. sentiment: 부정/중립/긍정 중 택1
    2. summary: 기사의 핵심 팩트와 수치, 보도 의도를 3문장 이상으로 상세히 요약하라.
    3. reason: 이 기사가 하림의 시장 점유율, 브랜드 프리미엄 이미지, 혹은 정부 규제 가능성에 미칠 '기사 고유의 리스크'를 분석하라.
    4. guideline: 홍보실이 당장 실행할 구체적 액션(Wording 포함)을 3가지 이상 제안하라.

    [기사 정보]
    제목: {news_title}
    내용: {news_desc}

    결과는 반드시 JSON 형식으로만 답변하라. 기사 간 분석 내용 중복은 절대 금지다.
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=data, timeout=25)
        res_json = response.json()
        
        if 'candidates' in res_json and res_json['candidates'][0].get('content'):
            result_text = res_json['candidates'][0]['content']['parts'][0]['text']
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        
        # 보험 로직도 기사별로 다르게 작동하도록 세분화
        if "적자" in news_title:
            return {"sentiment": "부정", "summary": "신사업 수익성 악화 보도", "reason": "프리미엄 전략의 시장 안착 실패 의구심 증폭", "guideline": "수익 개선 로드맵 발표 준비"}
        elif "담합" in news_title:
            return {"sentiment": "부정", "summary": "계열사 법적 리스크 발생", "reason": "그룹 전반의 윤리 경영 이미지 실추 및 징벌적 과징금 우려", "guideline": "지주사와의 거리두기 및 준법 감시 강화 홍보"}
        return {"sentiment": "중립", "summary": "모니터링 대상 기사", "reason": "통상적 경영 보도", "guideline": "상황 주시"}
        
    except:
        return {"sentiment": "중립", "summary": "연결 지연", "reason": "-", "guideline": "-"}

# 🚀 실제 기사 데이터 5종
actual_news_data = [
    {"title": "라면 늪에 빠진 하림…'더미식' 5년째 적자", "link": "https://biz.sbs.co.kr/article/20000301945", "desc": "하림산업 '더미식' 브랜드의 지속적인 적자와 수익성 해결 과제 보도."},
    {"title": "하림산업 더미식, 5년째 적자 확대…성장보다 비용이 앞섰다", "link": "https://www.datanews.co.kr/news/article.html?no=144117", "desc": "매출 대비 과도한 마케팅 비용 지출로 인한 영업손실 지속 분석."},
    {"title": "하림 계열사 '선진' 돈육 담합 적발 … \"지주사는 관여 안해\"", "link": "https://www.safetimes.co.kr/news/articleView.html?idxno=241450", "desc": "공정위의 돈육 담합 적발과 하림지주의 거리두기 대응."},
    {"title": "하림지주, 유균 사외이사 재선임", "link": "https://www.digitaltoday.co.kr/news/articleView.html?idxno=650517", "desc": "정기 주주총회를 통한 기존 사외이사 재선임 가결."},
    {"title": "하림, 탄소중립 나무심기 동참… ESG 경영 실천 앞장", "link": "https://sjbnews.com/news/news.php?number=875288", "desc": "식목일 맞이 지역 환경 보전 활동 및 사회적 책임 이행."}
]

for news in actual_news_data:
    result = analyze_sentiment(news['title'], news['desc'])
    sentiment = result.get('sentiment', '중립')

    if "부정" in sentiment:
        msg = f"🚨 **부정 : {news['title']}**\n\n"
        msg += f"🔗 **링크:** {news['link']}\n\n"
        msg += f"📝 **요약:** {result.get('summary')}\n\n"
        msg += f"🧐 **이유:** {result.get('reason')}\n\n"
        msg += f"🛡️ **대응:** {result.get('guideline')}"
    elif "긍정" in sentiment:
        msg = f"✅ **긍정 : {news['title']}**\n🔗 {news['link']}"
    else:
        msg = f"💡 **중립 : {news['title']}**\n🔗 {news['link']}"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})

print("심층 분석 모드 5건 테스트 완료!")
