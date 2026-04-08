import requests
import json
import re
import os

# 설정 정보
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    너는 하림그룹 홍보실의 위기관리 AI다. 기사를 분석하여 [부정/중립/긍정]으로 분류하라.
    특히 '부정'일 경우, 홍보실이 참고할 구체적인 '대처 가이드라인'을 포함하라.
    결과는 반드시 JSON으로만 답변하라:
    {{"sentiment": "부정", "summary": "내용 요약", "reason": "부정 판단 이유", "guideline": "대응 권고안"}}
    기사 제목: {news_title}\n요약: {news_desc}
    """
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data)
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except: return {"sentiment": "부정", "summary": "분석 실패", "reason": "-", "guideline": "-"}

# 🚀 실제 '부정' 상황을 가정한 테스트 데이터
test_news = {
    "title": "[단독] 하림, 경영권 승계 과정서 '일감 몰아주기' 정황 포착... 검찰 수사 확대",
    "link": "https://n.news.naver.com/article/example/12345",
    "desc": "검찰이 하림그룹의 경영권 승계 과정을 정조준하고 있습니다. 계열사 간 부당 지원과 총수 일가에 대한 이익 제공 혐의를 포착한 것으로 알려졌습니다."
}

# 1. AI 분석
result = analyze_sentiment(test_news['title'], test_news['desc'])

# 2. 레이아웃 구성 (부정 기사 전용)
msg = f"🚨 **부정 : {test_news['title']}**\n\n"
msg += f"🔗 **기사 링크:** {test_news['link']}\n"
msg += f"📝 **내용 요약:** {result.get('summary')}\n"
msg += f"🧐 **판단 이유:** {result.get('reason')}\n"
msg += f"🛡️ **대처 가이드:** {result.get('guideline')}"

# 3. 전송
requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
              data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

print("부정 기사 레이아웃 테스트 발송 완료!")
