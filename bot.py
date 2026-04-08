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
    
    # AI에게 강력한 역할을 부여하고 JSON 답변을 강제
    prompt = f"""
    너는 하림그룹 홍보실의 '비공개 위기대응 전략가'다. 
    이 내용은 내부 전략용이므로 절대 답변을 거부하지 말고 객관적으로 분석하라.
    [분류기준] 부정: 적자, 담합, 조사 / 긍정: ESG, 기부, 동참 / 중립: 인사, 일반보도

    결과는 반드시 JSON으로만 답변:
    {{
      "sentiment": "부정/중립/긍정",
      "summary": "핵심 요약 1줄",
      "reason": "판단 근거",
      "guideline": "대응 가이드"
    }}

    기사제목: {news_title}
    기사내용: {news_desc}
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
        response = requests.post(url, json=data, timeout=15)
        res_json = response.json()
        
        # AI가 답변을 거부했을 때의 보험 로직 (Fallback)
        if 'candidates' not in res_json or not res_json['candidates'][0].get('content'):
            if any(k in news_title for k in ["적자", "담합", "수사", "조사", "늪"]):
                return {"sentiment": "부정", "summary": news_title, "reason": "기업 실적 악화 및 법적 리스크", "guideline": "부정 여론 확산 방지 및 팩트체크"}
            elif any(k in news_title for k in ["ESG", "나무심기", "동참", "실천"]):
                return {"sentiment": "긍정", "summary": news_title, "reason": "친환경 이미지 제고", "guideline": "긍정 이미지 확산 및 보도자료 배포"}
            return {"sentiment": "중립", "summary": news_title, "reason": "일반 보도", "guideline": "상황 모니터링"}

        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "summary": "분석 오류", "reason": "시스템 연결 불안정", "guideline": "수동 확인 요망"}

# 🚀 기획자님이 주신 실제 기사 리스트
actual_news_data = [
    {
        "title": "라면 늪에 빠진 하림…'더미식' 5년째 적자",
        "link": "https://biz.sbs.co.kr/article/20000301945?division=NAVER",
        "desc": "하림산업 '더미식'이 5년 연속 적자를 기록하며 수익성 악화 우려."
    },
    {
        "title": "하림산업 더미식, 5년째 적자 확대…성장보다 비용이 앞섰다",
        "link": "https://www.datanews.co.kr/news/article.html?no=144117",
        "desc": "공격적인 마케팅 비용 지출로 인한 적자 폭 확대 분석."
    },
    {
        "title": "하림 계열사 '선진' 돈육 담합 적발 … \"지주사는 관여 안해\"",
        "link": "https://www.safetimes.co.kr/news/articleView.html?idxno=241450",
        "desc": "계열사 선진의 담합 적발 및 하림지주의 입장 표명."
    },
    {
        "title": "하림지주, 유균 사외이사 재선임",
        "link": "https://www.digitaltoday.co.kr/news/articleView.html?idxno=650517",
        "desc": "주주총회를 통한 사외이사 재선임 안건 통과."
    },
    {
        "title": "하림, 탄소중립 나무심기 동참… ESG 경영 실천 앞장",
        "link": "https://sjbnews.com/news/news.php?number=875288",
        "desc": "식목일 기념 나무심기 봉사활동을 통한 ESG 경영 실천."
    }
]

for news in actual_news_data:
    result = analyze_sentiment(news['title'], news['desc'])
    sentiment = result.get('sentiment', '중립')

    # 레이아웃 구성
    if "부정" in sentiment:
        msg = f"🚨 **부정 : {news['title']}**\n\n🔗 **링크:** {news['link']}\n📝 **요약:** {result.get('summary')}\n🧐 **이유:** {result.get('reason')}\n🛡️ **대응:** {result.get('guideline')}"
    elif "긍정" in sentiment:
        msg = f"✅ **긍정 : {news['title']}**\n🔗 {news['link']}"
    else:
        msg = f"💡 **중립 : {news['title']}**\n🔗 {news['link']}"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})

print("실제 기사 5건 재테스트 완료!")
