import urllib.request
import json
import requests
import re
import os

# 🔑 설정 정보 (GitHub Secrets)
NAVER_CLIENT_ID = os.environ.get("NAVER_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

SENT_LOG = "sent_links.txt"

def analyze_sentiment(news_title, news_desc):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 AI에게 고강도 분석을 명령하는 프롬프트
    prompt = f"""
    너는 하림그룹 홍보실의 '수석 위기관리 전략가'이며, 보고 대상은 그룹 회장단이다. 
    뻔한 소리는 생략하고, 각 기사의 맥락을 짚어 아주 날카롭고 상세한 리포트를 작성하라.

    [분석 요구사항]
    1. sentiment: 부정/중립/긍정 중 택1
    2. summary: 기사의 표면적 사실을 넘어 보도 의도와 핵심 쟁점을 3문장 이상 상세 기술하라.
    3. reason: 이 보도가 하림의 브랜드 프리미엄 이미지, 시장 점유율, 혹은 법적 리스크에 미칠 기사 고유의 파급력을 분석하라.
    4. guideline: 홍보실이 즉시 실행할 '구체적인 커뮤니케이션 논리(Wording 포함)'와 대응 전략을 3가지 이상 상세히 제안하라.

    기사 제목: {news_title}
    기사 내용: {news_desc}

    결과는 반드시 JSON 형식으로만 답변하라. 기사별로 분석 내용이 중복되면 절대 안 된다.
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=data, timeout=25)
        res_json = response.json()
        
        if 'candidates' in res_json and res_json['candidates'][0].get('content'):
            result_text = res_json['candidates'][0]['content']['parts'][0]['text']
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        
        # [보험 로직] AI가 답변을 거부할 경우를 대비한 키워드별 심층 분기
        if any(k in news_title for k in ["적자", "늪", "손실"]):
            return {
                "sentiment": "부정",
                "summary": f"{news_title} 관련 보도로, 하림산업 신사업의 장기 적자 구조가 부각되며 시장의 회의적 시각이 확산될 우려가 있음.",
                "reason": "프리미엄 라면 시장 내 입지 구축 실패로 비춰질 수 있으며, 이는 그룹 전반의 신사업 추진 동력을 약화시킬 리스크가 큼.",
                "guideline": "1. '품질 경영' 가치 재조명 보도자료 배포 / 2. 수익성 개선을 위한 공정 효율화 계획 강조 / 3. 커뮤니티 내 부정 여론 확산 실시간 차단"
            }
        elif any(k in news_title for k in ["담합", "수사", "조사", "공정위"]):
            return {
                "sentiment": "부정",
                "summary": f"{news_title} 건으로, 계열사 선진의 법적 리스크가 그룹 지배구조 및 윤리 이미지에 타격을 주는 상황임.",
                "reason": "공정위 제재는 기업 평판에 치명적이며, 소비자 불매운동이나 ESG 등급 하락으로 이어질 가능성이 매우 높음.",
                "guideline": "1. '지주사 무관함'과 '계열사 독립 경영' 논리 강화 / 2. 그룹 차원의 준법 감시 시스템 업그레이드 선포 / 3. 대언론 팩트체크 세션 진행"
            }
        return {"sentiment": "중립", "summary": news_title, "reason": "일반 경영 보도", "guideline": "동향 주시"}
        
    except:
        return {"sentiment": "중립", "summary": "연결 지연", "reason": "-", "guideline": "-"}

# 1. 네이버 뉴스 검색
encText = urllib.parse.quote("하림")
url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=10&sort=date"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    news_data = json.loads(response.read().decode('utf-8'))
    
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, "r") as f:
            sent_links = f.read().splitlines()
    else:
        sent_links = []

    items = news_data.get('items', [])
    items.reverse() # 최신 기사가 아래로 오게 정렬

    for news in items:
        link = news['link']
        if link in sent_links: continue

        title = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        
        # 2. AI 분석 실행
        result = analyze_sentiment(title, news['description'])
        sentiment = result.get('sentiment', '중립')

        # 3. 레이아웃 (부정은 상세히, 긍정/중립은 콤팩트하게)
        if "부정" in sentiment:
            msg = f"🚨 **부정 : {title}**\n\n"
            msg += f"🔗 **링크:** {link}\n\n"
            msg += f"📝 **요약:** {result.get('summary')}\n\n"
            msg += f"🧐 **이유:** {result.get('reason')}\n\n"
            msg += f"🛡️ **대응:** {result.get('guideline')}"
        elif "긍정" in sentiment:
            msg = f"✅ **긍정 : {title}**\n🔗 {link}"
        else:
            msg = f"💡 **중립 : {title}**\n🔗 {link}"

        # 4. 전송 (disable_web_page_preview=False 로 이미지 노출)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})
        
        with open(SENT_LOG, "a") as f:
            f.write(link + "\n")

except Exception as e:
    print(f"오류: {e}")
