import urllib.request
import json
import requests
import re
import os

# 설정 정보
NAVER_CLIENT_ID = os.environ.get("NAVER_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

# [핵심] 이미 보낸 기사를 기억하기 위한 임시 파일 (GitHub Actions 환경 전용)
SENT_FILES_LOG = "sent_links.txt"

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"하림 홍보실 AI로서 기사 분석. [부정/중립/긍정] 분류 및 이유를 JSON으로 답변.\n제목: {news_title}\n내용: {news_desc}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data)
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "reason": "분석 실패"}

# 1. 네이버 뉴스 검색
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=10&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    # 이전에 보낸 링크들 불러오기 (중복 방지용)
    if os.path.exists(SENT_FILES_LOG):
        with open(SENT_FILES_LOG, "r") as f:
            sent_links = f.read().splitlines()
    else:
        sent_links = []

    new_sent_links = []
    
    for news in news_data['items']:
        link = news['link']
        
        # [중요] 이미 보낸 링크면 건너뛰기!
        if link in sent_links:
            continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        desc = news['description']
        
        # AI 분석
        result = analyze_sentiment(title, desc)
        sentiment = result.get('sentiment', '중립')

        # 레이아웃 분기
        if sentiment == "부정":
            msg = f"🚨🚨 **[위기 감지: 부정]** 🚨🚨\n\n🔥 **제목:** {title}\n🧐 **사유:** {result.get('reason','')}\n🔗 [원문보기]({link})"
        else:
            emoji = "✅" if sentiment == "긍정" else "💡"
            msg = f"{emoji} **[{sentiment}]** {title}\n🔗 [링크]({link})"

        # 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        new_sent_links.append(link)

    # 새로 보낸 링크 저장 (다음 번 실행 때 중복 방지)
    with open(SENT_FILES_LOG, "a") as f:
        for l in new_sent_links:
            f.write(l + "\n")

    if not new_sent_links:
        print("새로 올라온 기사가 없어 알림을 보내지 않았습니다.")

except Exception as e:
    print(f"오류: {e}")
