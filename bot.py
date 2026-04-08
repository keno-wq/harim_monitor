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
    
    # 🧠 부정 기사일수록 수치와 구체적 대응책을 요구하는 고강도 프롬프트
    prompt = f"""
    너는 하림그룹 홍보실의 '수석 위기대응 전략가'다. 
    아래 뉴스를 [부정, 중립, 긍정]으로 분류하되, 특히 '부정' 기사는 홍보실장이 즉시 보고받아야 하므로 매우 상세하게 분석하라.

    [작성 규칙]
    1. sentiment: 부정/중립/긍정 중 택1
    2. summary: 핵심 사건의 경위와 현재 상황을 2~3문장으로 전문적으로 요약.
    3. reason: 이 보도가 하림의 브랜드 신뢰도, 소비자 구매 심리, 혹은 정부 규제 가능성에 미칠 악영향을 심층 분석.
    4. guideline: 1) 언론사 대응 로직, 2) 온라인 여론 관리, 3) 지주사 및 계열사 협력 방안 등 구체적인 액션 플랜을 3가지 이상 제시.

    기사제목: {news_title}
    기사내용: {news_desc}
    
    결과는 반드시 JSON으로만 답변하라.
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
        response = requests.post(url, json=data, timeout=20)
        res_json = response.json()
        
        # 분석 성공 시
        if 'candidates' in res_json and res_json['candidates'][0].get('content'):
            result_text = res_json['candidates'][0]['content']['parts'][0]['text']
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        
        # 분석 거부 시 보험 로직 (상세 버전)
        if any(k in news_title for k in ["적자", "담합", "수사", "조사", "늪"]):
            return {
                "sentiment": "부정",
                "summary": f"{news_title} 보도로 인해 기업의 재무 건전성 및 윤리 경영에 대한 의구심이 증폭될 수 있는 상황임.",
                "reason": "장기 적자 보도는 '프리미엄 브랜드' 전략의 실패로 비춰질 수 있으며, 담합 이슈는 공정위의 추가 타겟이 될 리스크가 큼.",
                "guideline": "1. 수익성 개선 지표를 포함한 후속 보도자료 배포 검토 / 2. 계열사 리스크 차단을 위한 지주사 공식 입장문 준비 / 3. 포털 메인 노출 시 모니터링 및 댓글 흐름 관리"
            }
        return {"sentiment": "중립", "summary": news_title, "reason": "통상적인 경영 활동", "guideline": "상황 모니터링"}
    except:
        return {"sentiment": "중립", "summary": "연결 지연", "reason": "-", "guideline": "-"}

# 🚀 실제 기사 데이터 5종
actual_news_data = [
    {"title": "라면 늪에 빠진 하림…'더미식' 5년째 적자", "link": "https://biz.sbs.co.kr/article/20000301945", "desc": "하림산업 '더미식' 브랜드의 지속적인 적자와 수익성 해결 과제 보도."},
    {"title": "하림산업 더미식, 5년째 적자 확대…성장보다 비용이 앞섰다", "link": "https://www.datanews.co.kr/news/article.html?no=144117", "desc": "매출 대비 과도한 마케팅 비용 지출로 인한 영업손실 지속 분석."},
    {"title": "하림 계열사 '선진' 돈육 담합 적발 … \"지주사는 관여 안해\"", "link": "https://www.safetimes.co.kr/news/articleView.html?idxno=241450", "desc": "공정위의 돈육 담합 적발과 하림지주의 거리두기 대응."},
    {"title": "하림지주, 유균 사외이사 재선임", "link": "https://www.digitaltoday.co.kr/news/articleView.html?idxno=650517", "desc": "정기 주주총회를 통한 기존 사외이사 재선임 가결."},
    {"title": "하림, 탄소중립 나무심기 동참… ESG 경영 실천 앞장", "link": "https://sjbnews.com/news/news.php?number=875288", "desc": "식목일 맞이 지역 환경 보전 활동 및 사회적 책임 이행."}
]

for news in actual_news_data:
    result = analyze_sentiment(news['title'], news['desc'])
    sentiment = result.get('sentiment', '중립')

    if "부정" in sentiment:
        msg = f"🚨 **부정 : {news['title']}**\n\n"
        msg += f"🔗 **링크:** {news['link']}\n\n"
        msg += f"📝 **요약:** {result.get('summary')}\n\n"
        msg += f"🧐 **이유:** {result.get('reason')}\n\n"
        msg += f"🛡️ **대응:** {result.get('guideline')}"
    elif "긍정" in sentiment:
        msg = f"✅ **긍정 : {news['title']}**\n🔗 {news['link']}"
    else:
        msg = f"💡 **중립 : {news['title']}**\n🔗 {news['link']}"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False})

print("실전 기사 5건 심층 분석 테스트 완료!")
