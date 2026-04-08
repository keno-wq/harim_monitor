import urllib.request
import json
import requests
import re
import os

# 🔑 설정 정보 (GitHub Secrets 연동)
NAVER_CLIENT_ID = os.environ.get("NAVER_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

SENT_LOG = "sent_links.txt"

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 홍보실 전문가 페르소나 및 가이드라인 주입
    prompt = f"""
    너는 하림그룹 홍보실의 '리스크 관리 전문가'다. 아래 뉴스를 분석하여 [부정, 중립, 긍정]으로 분류하라.
    특히 '부정' 판단 시 홍보팀이 즉각 참고할 실무적인 대응안을 포함해야 한다.

    [분류 가이드라인]
    - 부정: 경영권 승계 의혹, 사익편취, 실적 악화, 자금난(PF), 공정위/법적 리스크, 위생 이슈, 소비자 불만.
    - 긍정: 사회공헌, 수상 소식, 실적 반등, 신제품 호평.
    - 중립: 단순 제품 출시, 일반적인 업계 동향 보도.

    반드시 아래 JSON 형식으로만 답변하라 (JSON 외 텍스트 금지):
    {{
      "sentiment": "부정/중립/긍정",
      "summary": "기사 핵심 내용 1줄 요약",
      "reason": "홍보실 관점에서의 판단 근거",
      "guideline": "홍보팀 실무 대응 권고안"
    }}

    기사 제목: {news_title}
    기사 내용: {news_desc}
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
        
        # AI 거절 또는 응답 오류 시 예외처리
        if 'candidates' not in res_json or not res_json['candidates'][0].get('content'):
            return {"sentiment": "중립", "summary": "분석 일시 제한", "reason": "AI가 민감 기사로 판단해 분석을 거부함", "guideline": "원문 직접 확인 필요"}

        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"sentiment": "중립", "summary": "데이터 형식 오류", "reason": "AI 응답 형식 이상", "guideline": "수동 모니터링"}
    except Exception as e:
        return {"sentiment": "중립", "summary": "연결 오류", "reason": str(e), "guideline": "잠시 후 재시도"}

# 1. 네이버 뉴스 검색 (최신 10개)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=10&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    # 중복 체크를 위한 로그 읽기
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, "r") as f:
            sent_links = f.read().splitlines()
    else:
        sent_links = []

    # 최신 기사가 텔레그램 맨 아래에 오도록 리스트 순서 뒤집기
    items = news_data.get('items', [])
    items.reverse() 

    new_links = []
    
    for news in items:
        link = news['link']
        if link in sent_links: continue

        # 텍스트 정제
        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        
        # 2. AI 분석 실행
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 분기
        if sentiment == "부정":
            msg = f"🚨 **부정 : {title}**\n\n"
            msg += f"🔗 **링크:** {link}\n"
            msg += f"📝 **요약:** {result.get('summary')}\n"
            msg += f"🧐 **이유:** {result.get('reason')}\n"
            msg += f"🛡️ **대응:** {result.get('guideline')}"
        elif sentiment == "긍정":
            msg = f"✅ **긍정 : {title}**\n🔗 {link}"
        else:
            msg = f"💡 **중립 : {title}**\n🔗 {link}"

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        new_links.append(link)

    # 발송 완료된 링크 저장
    with open(SENT_LOG, "a") as f:
        for l in new_links: f.write(l + "\n")

except Exception as e:
    print(f"시스템 오류: {e}")
