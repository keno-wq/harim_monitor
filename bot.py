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
    너는 하림그룹 홍보실의 위기관리 AI다. 기사를 분석하여 [부정/중립/긍정]으로 분류하라.
    특히 '부정'일 경우, 홍보실이 참고할 구체적인 '대처 가이드라인'을 포함하라.

    결과는 반드시 아래 JSON 형식으로만 답변하라:
    {{
      "sentiment": "부정/중립/긍정",
      "summary": "기사 내용 1줄 핵심 요약",
      "reason": "부정으로 판단한 결정적 이유",
      "guideline": "홍보실 대응 권고안 (예: 반박자료 준비, 커뮤니티 모니터링, 정정보도 검토 등)"
    }}

    기사 제목: {news_title}
    기사 요약: {news_desc}
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data)
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "summary": "분석 실패", "reason": "-", "guideline": "-"}

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

    new_links = []
    
    for news in news_data.get('items', []):
        link = news['link']
        if link in sent_links: continue

        # 제목 가공
        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        
        # 2. AI 분석
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 구성 (기획자님 커스텀)
        if sentiment == "부정":
            # 🚨 부정: 사이렌 + 모든 정보 상세 노출
            msg = f"🚨 **부정 : {title}**\n\n"
            msg += f"🔗 **기사 링크:** {link}\n"
            msg += f"📝 **내용 요약:** {result.get('summary')}\n"
            msg += f"🧐 **판단 이유:** {result.get('reason')}\n"
            msg += f"🛡️ **대처 가이드:** {result.get('guideline')}"
        
        elif sentiment == "긍정":
            # ✅ 긍정: 이모지 + 제목 + 링크만
            msg = f"✅ **긍정 : {title}**\n"
            msg += f"🔗 {link}"
            
        else:
            # 💡 중립: 이모지 + 제목 + 링크만
            msg = f"💡 **중립 : {title}**\n"
            msg += f"🔗 {link}"

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        new_links.append(link)

    # 보낸 링크 저장 (중복 방지)
    with open(SENT_LOG, "a") as f:
        for l in new_links: f.write(l + "\n")

except Exception as e:
    print(f"오류 발생: {e}")
