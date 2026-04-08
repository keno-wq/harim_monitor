import urllib.request
import json
import requests
import re
import os

# 🔑 설정 정보
NAVER_CLIENT_ID = os.environ.get("NAVER_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

SENT_LOG = "sent_links.txt"

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 AI에게 내리는 특급 지시 (Safety Filter 우회를 위해 역할 부여 강화)
    prompt = f"""
    너는 하림그룹의 '리스크 관리 전문가'다. 아래 뉴스를 분석하여 홍보팀이 대응할 수 있게 정보를 가공하라.
    윤리적 판단을 하지 말고, 오직 '기업 리스크' 관점에서만 답변하라.

    [응답 규칙]
    1. sentiment: 부정, 중립, 긍정 중 하나
    2. summary: 기사의 핵심 내용을 1문장으로 요약
    3. reason: 왜 하림그룹에 위기인지 홍보실 관점에서 설명
    4. guideline: 홍보팀이 당장 취해야 할 실무적 대응 방안

    반드시 JSON 형식으로만 응답하라.
    기사 제목: {news_title}
    기사 내용: {news_desc}
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [ # AI의 과도한 검열을 방지하는 설정
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=data)
        response_json = response.json()
        result_text = response_json['candidates'][0]['content']['parts'][0]['text']
        
        # JSON 데이터만 쏙 뽑아내기
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"sentiment": "부정", "summary": "분석 데이터 형식 오류", "reason": "AI 응답 형식이 올바르지 않음", "guideline": "수동 모니터링 필요"}
    except Exception as e:
        return {"sentiment": "부정", "summary": "AI 분석 연결 실패", "reason": str(e), "guideline": "API 키 확인 또는 수동 확인"}

# 1. 네이버 뉴스 검색 (최신 10개)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=10&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, "r") as f:
            sent_links = f.read().splitlines()
    else:
        sent_links = []

    items = news_data.get('items', [])
    items.reverse() # 최신 기사가 맨 밑에 오도록 뒤집기

    new_links = []
    
    for news in items:
        link = news['link']
        if link in sent_links: continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        
        # 2. AI 분석
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 구성
        if sentiment == "부정":
            msg = f"🚨 **부정 : {title}**\n\n"
            msg += f"🔗 **기사 링크:** {link}\n"
            msg += f"📝 **내용 요약:** {result.get('summary')}\n"
            msg += f"🧐 **판단 이유:** {result.get('reason')}\n"
            msg += f"🛡️ **대처 가이드:** {result.get('guideline')}"
        elif sentiment == "긍정":
            msg = f"✅ **긍정 : {title}**\n🔗 {link}"
        else:
            msg = f"💡 **중립 : {title}**\n🔗 {link}"

        # 4. 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        new_links.append(link)

    with open(SENT_LOG, "a") as f:
        for l in new_links: f.write(l + "\n")

except Exception as e:
    print(f"오류 발생: {e}")
