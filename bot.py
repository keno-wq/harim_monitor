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
    prompt = f"""너는 하림 홍보실 리스크 전문가다. 아래 뉴스를 [부정] 관점에서 분석해라. 
    반드시 JSON으로만 답변: {{"sentiment":"부정","summary":"요약","reason":"이유","guideline":"대응안"}}
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
        return {"sentiment": "부정", "summary": "긴급 리스크 발생", "reason": "경영 관련 중대 이슈", "guideline": "즉시 보고 및 대응"}

# 🚀 시뮬레이션용 부정 기사 5개 (오래된 순 -> 최신순 정렬)
test_news_list = [
    {
        "title": "[1보] 하림 공정위 현장조사 착수... 일감 몰아주기 의혹 다시 수면 위로",
        "link": "https://n.news.naver.com/article/001/0000001", # 테스트용 가상링크
        "desc": "공정거래위원회가 하림그룹 본사에 대한 현장조사에 나섰습니다. 승계 과정에서의 부당 지원 여부를 들여다보는 것으로 알려졌습니다."
    },
    {
        "title": "하림, 양재동 물류단지 개발 사업 'PF 자금난' 직격탄... 착공 연기 우려",
        "link": "https://n.news.naver.com/article/001/0000002",
        "desc": "하림그룹의 숙원 사업인 양재동 물류단지 개발이 최근 고금리와 PF 대출 경색으로 자금 조달에 난항을 겪고 있습니다."
    },
    {
        "title": "소비자원 \"하림 일부 냉동치킨 제품서 이물질 검출... 위생 관리 도마\"",
        "link": "https://n.news.naver.com/article/001/0000003",
        "desc": "하림의 인기 냉동 치킨 제품에서 비닐 이물질이 발견되었다는 소비자 신고가 접수되어 보건 당국이 조사에 나섰습니다."
    },
    {
        "title": "[특징주] 하림, 실적 부진에 주가 10% 급락... 'HMM 인수 포기 여파 지속'",
        "link": "https://n.news.naver.com/article/001/0000004",
        "desc": "하림의 분기 영업이익이 전년 대비 반토막 났습니다. 시장에서는 무리한 사업 확장 시도에 따른 후폭풍이라는 분석이 나옵니다."
    },
    {
        "title": "[단독] 하림, 경영권 승계 과정서 '편법 증여' 정황 포착... 검찰 수사 착수",
        "link": "https://n.news.naver.com/article/001/0000005",
        "desc": "검찰이 하림그룹 총수 일가의 사익 편취 및 편법 승계 의혹에 대해 강제 수사를 시작했습니다. 압수수색 범위가 확대될 전망입니다."
    }
]

for news in test_news_list:
    result = analyze_sentiment(news['title'], news['desc'])
    
    msg = f"🚨 **부정 : {news['title']}**\n\n"
    msg += f"🔗 **링크:** {news['link']}\n"
    msg += f"📝 **요약:** {result.get('summary')}\n"
    msg += f"🧐 **이유:** {result.get('reason')}\n"
    msg += f"🛡️ **대응:** {result.get('guideline')}"

    # disable_web_page_preview=False 로 설정하여 이미지가 나오게 함
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})

print("5건의 부정 기사 테스트 발송 완료!")
