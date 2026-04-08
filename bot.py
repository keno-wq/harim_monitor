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

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    너는 하림그룹 홍보실 AI다. 기사를 [부정/중립/긍정]으로 분류해라.
    결과는 반드시 JSON으로만: {{"sentiment": "분류", "category": "이슈명", "reason": "이유"}}
    기사 제목: {news_title}\n요약: {news_desc}
    """
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data)
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "category": "기타", "reason": "분석 일시 오류"}

# 1. 네이버에서 기사 5개를 넉넉하게 가져옵니다. (동시 발생 대비)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=5&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    # 2. 가져온 기사들을 하나씩 분석합니다.
    for news in news_data['items']:
        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        link = news['link']
        desc = news['description']

        # [참고] 원래는 '이미 보낸 기사인지' 체크하는 DB가 필요하지만,
        # 지금은 1분마다 실행되므로, 분석 후 텔레그램으로 보냅니다.
        # (중복 알림이 올 경우 나중에 필터 기능을 추가해 드릴게요!)

        result = analyze_sentiment(title, desc)
        sentiment = result.get('sentiment', '중립')
        emoji = "🚨" if sentiment == "부정" else "💡" if sentiment == "중립" else "✅"

        msg = f"{emoji} **[하림 AI 모니터링: {sentiment}]**\n\n📌 **제목:** {title}\n📂 **분류:** {result.get('category', '기타')}\n📝 **사유:** {result.get('reason', '분석 완료')}\n\n🔗 [기사 원문 보기]({link})"
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        print(f"전송 완료: {title[:15]}...")

except Exception as e:
    print(f"오류 발생: {e}")
