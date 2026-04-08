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
    prompt = f"""
    하림그룹 리스크 관리 전문가로서 아래 기사를 분석하라.
    [부정]판단 기준: 승계, 공정위, 수사, 자금난, PF, 위생 이슈 등.
    반드시 JSON으로만 답변: {{"sentiment":"부정/중립/긍정","summary":"요약","reason":"판단이유","guideline":"대응안"}}
    제목: {news_title}\n내용: {news_desc}
    """
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
    }
    try:
        response = requests.post(url, json=data, timeout=15)
        res_json = response.json()
        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        # AI 분석 실패 시 제목 기반 보험 로직
        is_bad = any(x in news_title for x in ['승계', '수사', '공정위', '의혹', '조사', 'PF', '자금'])
        return {
            "sentiment": "부정" if is_bad else "중립",
            "summary": "긴급 모니터링 필요",
            "reason": "AI 분석 지연으로 인한 자동 분류",
            "guideline": "원문 확인 후 비상 보고 체계 가동"
        }

# 1. 뉴스 검색
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
    items.reverse() # 최신 기사가 아래로!

    for news in items:
        link = news['link']
        if link in sent_links: continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        
        # 2. AI 분석
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 (부정은 사이렌, 긍정/중립은 깔끔하게)
        if sentiment == "부정":
            msg = f"🚨 **부정 : {title}**\n\n"
            msg += f"🔗 **링크:** {link}\n"
            msg += f"📝 **요약:** {result.get('summary')}\n"
            msg += f"🧐 **이유:** {result.get('reason')}\n"
            msg += f"🛡️ **대응:** {result.get('guideline')}"
        else:
            emoji = "✅" if sentiment == "긍정" else "💡"
            msg = f"{emoji} **{sentiment}** : {title}\n"
            msg += f"🔗 {link}"

        # 4. 텔레그램 전송 (Link Preview 활성화로 이미지 노출)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})
        
        with open(SENT_LOG, "a") as f:
            f.write(link + "\n")

except Exception as e:
    print(f"오류: {e}")
