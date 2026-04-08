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
    # 최신 Gemini 모델 주소
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 기획자님의 가이드라인을 상세하게 주입한 프롬프트
    prompt = f"""
    너는 하림그룹 홍보실의 '위기관리 AI 모니터링 에이전트'다.
    제시된 기사의 제목과 내용을 바탕으로 [부정 / 중립 / 긍정]을 엄격히 판별하라.

    [판단 가이드라인]
    1. 부정: 경영권 승계 의혹, 사익편취, 실적 악화, 신사업(더미식 등) 적자, 부동산 PF 자금 우려, 공정위 제재, 법적 분쟁, 위생 및 이물질 이슈.
    2. 중립: 단순한 사업 보도, 업계 동향 내 언급, 단순 신제품 출시 알림 중 비판적 내용이 없는 경우.
    3. 긍정: 사회 공헌 활동(CSR), 수상 소식, 실적 반등, 획기적인 신제품 호평 기사.

    결과는 반드시 아래 JSON 형식으로만 답변하고 다른 설명은 하지 마라:
    {{"sentiment": "부정/중립/긍정", "category": "이슈종류", "reason": "이유 1문장"}}

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

# 1. 네이버 뉴스 검색 (가장 최신 기사 1개)
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=1&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    if not news_data['items']:
        print("검색된 기사가 없습니다.")
    else:
        news = news_data['items'][0]
        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        link = news['link']
        desc = news['description']

        # 2. AI 분석 실행
        result = analyze_sentiment(title, desc)
        sentiment = result.get('sentiment', '중립')

        # 3. 감정에 따른 이모지 설정
        emoji = "🚨" if sentiment == "부정" else "💡" if sentiment == "중립" else "✅"

        # 4. 텔레그램 메시지 구성
        msg = f"{emoji} **[하림 AI 모니터링: {sentiment}]**\n\n"
        msg += f"📌 **제목:** {title}\n"
        msg += f"📂 **분류:** {result.get('category', '기타')}\n"
        msg += f"📝 **사유:** {result.get('reason', '분석 완료')}\n\n"
        msg += f"🔗 [기사 원문 보기]({link})"
        
        # 버튼 (현재는 디자인용이며, 실제 작동하려면 별도의 수신 서버가 필요합니다)
        reply_markup = {
            "inline_keyboard": [[
                {"text": "👍 판단 맞음", "callback_data": "correct"},
                {"text": "👎 오판", "callback_data": "incorrect"}
            ]]
        }

        # 5. 모든 기사 전송 (조건문 제거됨)
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(reply_markup)
        }
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=payload)
        print(f"분석 완료 및 알림 전송: [{sentiment}]")

except Exception as e:
    print(f"오류 발생: {e}")
