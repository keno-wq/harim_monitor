import urllib.request
import json
import requests
import re
import os

# 🔑 설정 정보 (Secrets에서 가져오기)
NAVER_CLIENT_ID = os.environ.get("NAVER_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    너는 하림그룹 홍보실 AI다. 기사를 [부정/중립/긍정]으로 분류해라.
    결과는 반드시 JSON으로만 답변해라.
    기사 제목: {news_title}\n요약: {news_desc}
    """
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data)
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "reason": "분석 오류"}

# 1. 네이버 뉴스 검색 (최신 5개)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=5&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    for news in news_data['items']:
        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        link = news['link']
        desc = news['description']

        # 2. AI 분석
        result = analyze_sentiment(title, desc)
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 분기 처리 (기획자님 요청 사항)
        if sentiment == "부정":
            # [부정] 크게, 상세하게 노출
            msg = f"🚨🚨 **[위기 감지: 부정 기사]** 🚨🚨\n\n"
            msg += f"🔥 **제목:** {title}\n"
            msg += f"🚩 **분류:** {result.get('category', '위기이슈')}\n"
            msg += f"🧐 **분석 사유:** {result.get('reason', '가이드라인 위반 가능성')}\n\n"
            msg += f"🔗 [지금 바로 원문 확인하기]({link})"
        else:
            # [중립/긍정] 콤팩트하게 노출
            emoji = "✅" if sentiment == "긍정" else "💡"
            msg = f"{emoji} **[{sentiment}]** {title}\n"
            msg += f"🔗 [링크]({link})"

        # 4. 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})

except Exception as e:
    print(f"오류 발생: {e}")
