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
    
    # 🧠 AI 지시사항 보강 (더 구체적으로)
    prompt = f"""
    너는 기업 홍보실의 뉴스 분석가다. 아래 기사를 [부정, 중립, 긍정] 중 하나로 분류하라.
    기사 제목: {news_title}
    기사 내용: {news_desc}

    [분류 기준]
    - 부정: 하림의 기업 이미지 훼손, 법적 리스크, 위생 문제, 부정적 이슈 제기
    - 긍정: 사회공헌, 실적 호조, 신제품 찬사
    - 중립: 일반적인 제품 출시, 단순 업계 동향 보도

    반드시 아래 JSON 형식으로만 답하라:
    {{"sentiment": "분류결과", "summary": "요약", "reason": "이유", "guideline": "대응안"}}
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
        response = requests.post(url, json=data, timeout=10)
        res_data = response.json()
        
        # AI가 답변을 거부한 경우 처리
        if 'candidates' not in res_data or not res_data['candidates'][0].get('content'):
            return {"sentiment": "중립", "summary": "AI가 민감한 내용으로 판단해 분석을 거부함", "reason": "검열로 인한 분석 불가", "guideline": "원문 확인 권장"}
            
        result_text = res_data['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"sentiment": "중립", "summary": "데이터 형식 오류", "reason": "AI 응답 형식 이상", "guideline": "수동 확인"}
    except Exception as e:
        return {"sentiment": "중립", "summary": "연결 일시 오류", "reason": str(e), "guideline": "재실행 대기"}

# 1. 네이버 뉴스 검색
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
    items.reverse() # 최신 기사가 아래로 오게 정렬

    new_links = []
    
    for news in items:
        link = news['link']
        if link in sent_links: continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        
        # 2. AI 분석
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 (요청하신 형식)
        if sentiment == "부정":
            msg = f"🚨 **부정 : {title}**\n\n🔗 **기사 링크:** {link}\n📝 **내용 요약:** {result.get('summary')}\n🧐 **판단 이유:** {result.get('reason')}\n🛡️ **대처 가이드:** {result.get('guideline')}"
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
    print(f"오류: {e}")
