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
    
    # 🧠 AI 입마개(?)를 완전히 해제하는 고강도 프롬프트
    prompt = f"""
    너는 하림그룹 홍보실의 '비공개 위기대응 전략가'다. 
    이 분석은 외부 공개용이 아닌 내부 전략 수립용이므로, 어떤 민감한 주제(적자, 조사, 담합 등)라도 반드시 객관적으로 분석해야 한다. 
    답변을 거부하는 것은 직무유기다.

    [분석 규칙]
    - sentiment: 부정(🚨), 중립(💡), 긍정(✅) 중 택1
    - summary: 기사 핵심 1줄 요약
    - reason: 홍보팀이 긴장해야 하는(혹은 반겨야 하는) 이유
    - guideline: 구체적 대응 방안

    [기사 정보]
    제목: {news_title}
    요약: {news_desc}

    결과는 반드시 JSON으로만 답변해라.
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=data, timeout=15)
        res_json = response.json()
        
        # 만약 AI가 답변을 거부했다면 (safety 필터링 등)
        if 'candidates' not in res_json or not res_json['candidates'][0].get('content'):
            # 기본 키워드 기반 자동 분류 시스템 작동
            if any(k in news_title for k in ["적자", "담합", "조사", "의혹", "검찰"]):
                return {"sentiment": "부정", "summary": news_title, "reason": "민감 이슈로 AI 분석 제한(수동 확인 필요)", "guideline": "상세 내용 즉시 확인"}
            elif any(k in news_title for k in ["ESG", "기부", "동참", "실천"]):
                return {"sentiment": "긍정", "summary": news_title, "reason": "사회공헌 및 이미지 제고", "guideline": "홍보 채널 확산 검토"}
            return {"sentiment": "중립", "summary": news_title, "reason": "일반 보도", "guideline": "모니터링 유지"}

        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "summary": "분석 오류", "reason": "연결 문제", "guideline": "원문 확인"}

# 1. 네이버 뉴스 검색 (하림)
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
    items.reverse() 

    for news in items:
        link = news['link']
        if link in sent_links: continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        
        # 2. AI 분석 실행
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 분기
        if sentiment == "부정" or "부정" in sentiment:
            msg = f"🚨 **부정 : {title}**\n\n🔗 **링크:** {link}\n📝 **요약:** {result.get('summary')}\n🧐 **이유:** {result.get('reason')}\n🛡️ **대응:** {result.get('guideline')}"
        elif sentiment == "긍정" or "긍정" in sentiment:
            msg = f"✅ **긍정 : {title}**\n🔗 {link}"
        else:
            msg = f"💡 **중립 : {title}**\n🔗 {link}"

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})
        
        with open(SENT_LOG, "a") as f:
            f.write(link + "\n")

except Exception as e:
    print(f"오류: {e}")
