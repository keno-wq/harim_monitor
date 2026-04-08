import urllib.request
import json
import requests
import re
import os

# 깃허브 금고(Secrets)에서 비밀번호를 자동으로 가져옵니다.
NAVER_CLIENT_ID = os.environ.get("NAVER_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

def analyze_sentiment(news_title, news_desc):
    # 구글 Gemini AI 서버 연결
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    너는 하림그룹 홍보실의 '위기관리 AI 모니터링 에이전트'다.
    입력되는 기사 제목과 요약을 분석하여 [부정 / 중립 / 긍정] 중 하나로 분류해라.
    결과는 반드시 JSON 형식으로만 답변해라.
    
    [핵심 부정 판단 기준]
    1. 경영권 승계 관련 비판 및 의혹
    2. 실적 악화 및 신사업 부진
    3. 부동산 개발(PF) 리스크
    4. 공정위 제재 및 법적 리스크
    5. 위생 및 품질 논란
    
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
        return {"sentiment": "중립", "reason": "분석 실패"}

# 1. 네이버 뉴스 검색 (최신 기사 1개)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=1&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    news = news_data['items'][0]
    
    title = news['title'].replace('<b>', '').replace('</b>', '')
    link = news['link']
    desc = news['description']

    # 2. AI 분석 실행
    result = analyze_sentiment(title, desc)

    # 3. 부정 기사일 경우 텔레그램 알림 (테스트를 위해 필요시 "부정"을 "긍정"으로 바꿔보세요)
    if result['sentiment'] == "부정":
        msg = f"🚨 **[하림 위기감지 AI 알림]**\n\n"
        msg += f"📌 **제목:** {title}\n"
        msg += f"📝 **사유:** {result.get('reason', '가이드라인 위반 감지')}\n\n"
        msg += f"🔗 [원문보기]({link})"
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        print("알림 전송 완료")
    else:
        print(f"이상 없음: {result['sentiment']}")

except Exception as e:
    print(f"오류 발생: {e}")
