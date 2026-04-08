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

# 중복 알림 방지를 위한 임시 저장 파일명
SENT_LOG = "sent_links.txt"

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 강화된 하림 전용 가이드라인 프롬프트
    prompt = f"""
    너는 하림그룹 홍보실의 '베테랑 위기관리 전문가'다. 
    제시된 기사를 분석하여 하림의 기업 가치나 평판에 해가 되면 무조건 [부정]으로 분류해라.

    [엄격한 판단 기준]
    1. 부정(🚨): '승계', '편법', '의혹', '공정위', '조사', '검찰', '적자', '부진', 'PF', '자금난', '위생', '불만', '담합' 등이 포함된 경우.
    2. 긍정(✅): '기부', '상생', '신제품 호평', '수상', '실적 반등', 'ESG 경영' 관련 소식.
    3. 중립(💡): 단순한 사실 보도, 단순 신제품 출시 알림, 일반적인 업계 동향.

    결과는 반드시 아래 JSON 형식으로만 답변해라:
    {{"sentiment": "부정/중립/긍정", "category": "이슈종류", "reason": "홍보실 관점에서의 분석 이유 1문장"}}

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
        return {"sentiment": "중립", "category": "기타", "reason": "분석 엔진 일시 오류"}

# 1. 네이버 뉴스 검색 (동시 발생 대비 10개까지 확인)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=10&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    # 이전에 보낸 링크 목록 가져오기 (중복 방지)
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, "r") as f:
            sent_links = f.read().splitlines()
    else:
        sent_links = []

    new_links = []
    
    for news in news_data.get('items', []):
        link = news['link']
        
        # 이미 보낸 기사는 패스!
        if link in sent_links:
            continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        desc = news['description']

        # 2. AI 분석 실행
        result = analyze_sentiment(title, desc)
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 분기 (부정은 크게, 나머지는 콤팩트하게)
        if sentiment == "부정":
            msg = f"🚨🚨 **[위기 감지: 부정 기사]** 🚨🚨\n\n"
            msg += f"🔥 **제목:** {title}\n"
            msg += f"🚩 **분류:** {result.get('category', '위기이슈')}\n"
            msg += f"🧐 **사유:** {result.get('reason', '가이드라인 위반 확인 필요')}\n\n"
            msg += f"🔗 [지금 바로 원문 확인]({link})"
        else:
            emoji = "✅" if sentiment == "긍정" else "💡"
            msg = f"{emoji} **[{sentiment}]** {title}\n"
            msg += f"🔗 [링크]({link})"

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        new_links.append(link)

    # 새로 보낸 기사 링크 저장
    with open(SENT_LOG, "a") as f:
        for l in new_links:
            f.write(l + "\n")

    print(f"작업 완료: {len(new_links)}건의 새로운 알림 발송")

except Exception as e:
    print(f"오류 발생: {e}")
