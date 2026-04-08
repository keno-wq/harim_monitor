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
    너는 하림그룹 홍보실의 '리스크 관리 전문가'다. 아래 뉴스를 분석하여 [부정, 중립, 긍정]으로 분류하라.
    반드시 아래 JSON 형식으로만 답변하라:
    {{
      "sentiment": "부정/중립/긍정",
      "summary": "핵심 요약 1문장",
      "reason": "판단 근거",
      "guideline": "홍보팀 대응 권고안"
    }}
    기사제목: {news_title}\n내용: {news_desc}
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
        # AI 거절 시 대비한 수동 로직 (보험)
        if 'candidates' not in res_json or not res_json['candidates'][0].get('content'):
            return {"sentiment": "부정" if "승계" in news_title or "수사" in news_title else "중립", 
                    "summary": news_title, "reason": "AI 분석 제한", "guideline": "원문 확인 필요"}
        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "summary": "오류", "reason": "-", "guideline": "-"}

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
    items.reverse() 

    for news in items:
        link = news['link']
        if link in sent_links: continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        
        # 2. AI 분석
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 메시지 및 이미지 처리
        # 네이버 뉴스 검색결과에는 직접적인 이미지 URL이 없으므로, 
        # 텔레그램의 Link Preview 기능을 극대화하거나 기사 원문에서 썸네일을 추측하도록 구성합니다.
        
        if sentiment == "부정":
            msg = f"🚨 **부정 : {title}**\n\n"
            msg += f"🔗 **링크:** {link}\n"
            msg += f"📝 **요약:** {result.get('summary')}\n"
            msg += f"🧐 **이유:** {result.get('reason')}\n"
            msg += f"🛡️ **대응:** {result.get('guideline')}"
        else:
            emoji = "✅" if sentiment == "긍정" else "💡"
            msg = f"{emoji} **[{sentiment}]** {title}\n🔗 {link}"

        # 4. 텔레그램 전송 (이미지가 잘 보이도록 설정)
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False  # 이 설정이 True면 이미지가 안 나옵니다. 반드시 False!
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=payload)
        
        with open(SENT_LOG, "a") as f:
            f.write(link + "\n")

except Exception as e:
    print(f"오류: {e}")
