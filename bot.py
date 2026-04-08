import requests
import json
import re
import os

# 🔑 설정 정보 (테스트용)
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""너는 하림 홍보실 리스크 전문가다. 아래 기사를 분석해라. 
    반드시 JSON으로만 답해라: {{"sentiment":"부정","summary":"요약","reason":"이유","guideline":"대응안"}}
    기사제목: {news_title}\n내용: {news_desc}"""
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
    }
    try:
        response = requests.post(url, json=data, timeout=15)
        res_json = response.json()
        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "부정", "summary": "분석 실패", "reason": "에러", "guideline": "수동확인"}

# 🚀 테스트용 가짜 부정 기사 데이터
test_news = {
    "title": "[단독] 하림, 경영권 승계 과정서 '일감 몰아주기' 정황 포착... 검찰 수사 확대",
    "link": "https://n.news.naver.com/article/example/12345",
    "desc": "검찰이 하림그룹 지배구조 강화 과정에서의 계열사 간 부당지원 및 사익 편취 의혹에 대해 강제 수사에 착수함."
}

# 분석 및 전송
result = analyze_sentiment(test_news['title'], test_news['desc'])

msg = f"🚨 **부정 : {test_news['title']}**\n\n"
msg += f"🔗 **링크:** {test_news['link']}\n"
msg += f"📝 **요약:** {result.get('summary')}\n"
msg += f"🧐 **이유:** {result.get('reason')}\n"
msg += f"🛡️ **대응:** {result.get('guideline')}"

requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
              data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

print("부정 기사 테스트 발송 완료!")
