import requests
import json
import re
import os

# 🔑 설정 정보
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""너는 하림 홍보실 리스크 전문가다. 아래 뉴스를 분석하여 [부정, 중립, 긍정] 분류와 대응안을 JSON으로만 답해라.
    {{
      "sentiment": "부정/중립/긍정",
      "summary": "1줄 요약",
      "reason": "판단 근거",
      "guideline": "홍보팀 대응 가이드"
    }}
    기사제목: {news_title}\n요약: {news_desc}"""
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
        ]
    }
    try:
        response = requests.post(url, json=data, timeout=15)
        res_json = response.json()
        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {"sentiment": "부정", "summary": "분석 오류", "reason": "민감 이슈", "guideline": "수동 확인"}

# 🚀 기획자님이 주신 실제 뉴스 데이터 (역순 배치: 최신이 아래로)
real_news_list = [
    {
        "title": "라면 늪에 빠진 하림…'더미식' 5년째 적자",
        "link": "https://biz.sbs.co.kr/article/20000301945?division=NAVER",
        "desc": "하림산업의 프리미엄 라면 브랜드 '더미식'이 5년 연속 적자를 기록하며 수익성 악화 우려가 커지고 있습니다."
    },
    {
        "title": "하림산업 더미식, 5년째 적자 확대…성장보다 비용이 앞섰다",
        "link": "https://www.datanews.co.kr/news/article.html?no=144117",
        "desc": "공격적인 마케팅 비용 지출에도 불구하고 매출 성장이 기대에 미치지 못하며 적자 폭이 확대되고 있다는 분석입니다."
    },
    {
        "title": "하림 계열사 '선진' 돈육 담합 적발 … \"지주사는 관여 안해\"",
        "link": "https://www.safetimes.co.kr/news/articleView.html?idxno=241450",
        "desc": "계열사 선진이 돈육 가격 담합으로 적발되었으나 하림지주는 지주사의 관여는 없었다며 선을 그었습니다."
    },
    {
        "title": "하림지주, 유균 사외이사 재선임",
        "link": "https://www.digitaltoday.co.kr/news/articleView.html?idxno=650517",
        "desc": "하림지주가 주주총회를 통해 기존 유균 사외이사를 재선임하기로 결정했습니다."
    },
    {
        "title": "하림, 탄소중립 나무심기 동참… ESG 경영 실천 앞장",
        "link": "https://sjbnews.com/news/news.php?number=875288",
        "desc": "제81회 식목일을 맞아 새만금환경생태단지에서 탄소중립 실천을 위한 나무심기 봉사활동을 진행했습니다."
    }
]

for news in real_news_list:
    result = analyze_sentiment(news['title'], news['desc'])
    sentiment = result.get('sentiment', '중립')
    
    if sentiment == "부정":
        msg = f"🚨 **부정 : {news['title']}**\n\n"
        msg += f"🔗 **링크:** {news['link']}\n"
        msg += f"📝 **요약:** {result.get('summary')}\n"
        msg += f"🧐 **이유:** {result.get('reason')}\n"
        msg += f"🛡️ **대응:** {result.get('guideline')}"
    elif sentiment == "긍정":
        msg = f"✅ **긍정 : {news['title']}**\n🔗 {news['link']}"
    else:
        msg = f"💡 **중립 : {news['title']}**\n🔗 {news['link']}"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})

print("실제 기사 5건 시뮬레이션 완료!")
