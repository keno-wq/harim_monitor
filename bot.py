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
    prompt = f"하림 홍보실 AI로서 기사 분석. [부정/중립/긍정] 분류 및 이유를 JSON으로 답변.\n제목: {news_title}\n내용: {news_desc}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data)
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "중립", "reason": "분석 실패"}

# 🚀 테스트용 가짜 기사 데이터 3종 세트
test_news = [
    {
        "title": "[단독] 하림, 승계 과정서 편법 증여 의혹 제기... 공정위 조사 착수",
        "link": "https://www.google.com",
        "desc": "하림그룹의 경영권 승계 과정에서 일감 몰아주기와 편법 증여가 있었다는 의혹이 제기되어 파장이 일고 있습니다."
    },
    {
        "title": "하림, 삼계탕 등 간편식 신제품 3종 출시",
        "link": "https://www.google.com",
        "desc": "하림이 여름 성수기를 맞아 집에서 간편하게 즐길 수 있는 보양식 신제품을 선보입니다."
    },
    {
        "title": "하림, 지역 소외계층 위해 닭고기 1,000세트 기부 '훈훈'",
        "link": "https://www.google.com",
        "desc": "하림이 전북 지역 어려운 이웃들을 위해 나눔 활동을 펼치며 ESG 경영을 실천하고 있습니다."
    }
]

for news in test_news:
    title = news['title']
    link = news['link']
    desc = news['desc']
    
    # AI 분석
    result = analyze_sentiment(title, desc)
    sentiment = result.get('sentiment', '중립')

    # 레이아웃 분기 (기획자님 요청사항 반영)
    if sentiment == "부정":
        msg = f"🚨🚨 **[위기 감지: 부정 기사]** 🚨🚨\n\n"
        msg += f"🔥 **제목:** {title}\n"
        msg += f"🚩 **분류:** {result.get('category', '위기이슈')}\n"
        msg += f"🧐 **분석 사유:** {result.get('reason', '가이드라인 위반 감지')}\n\n"
        msg += f"🔗 [지금 바로 원문 확인하기]({link})"
    else:
        emoji = "✅" if sentiment == "긍정" else "💡"
        msg = f"{emoji} **[{sentiment}]** {title}\n"
        msg += f"🔗 [링크]({link})"

    # 전송
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

print("테스트 알림 3종 발송 완료!")
