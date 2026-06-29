from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["tools"])


class ToolInfo(BaseModel):
    name: str = Field(..., description="도구의 이름")
    description: str = Field(..., description="도구에 대한 상세 설명")
    category: str = Field(..., description="도구의 분류 (예: 이메일, 일정, 분석 등)")


@router.get("/tools", response_model=List[ToolInfo])
def get_tools():
    """
    Naruon AI 이메일 워크스페이스에서 사용할 수 있는 분석 및 실행 도구 목록을 반환합니다.
    """
    return [
        {
            "name": "이메일 맥락 요약 (Thread Summarizer)",
            "description": "긴 이메일 스레드를 분석하여 핵심 맥락, 결정 사항, 미해결 질문을 추출합니다.",
            "category": "이메일 분석",
        },
        {
            "name": "실행 항목 자동 추출 (Action Item Extractor)",
            "description": "이메일 본문에서 사용자가 수행해야 할 작업(Task)과 마감일을 자동으로 식별합니다.",
            "category": "작업 관리",
        },
        {
            "name": "발신자 관계 분석 (Sender DAG Analytics)",
            "description": "과거 이메일 기록을 바탕으로 발신자와의 관계(조직도 상 위치, 중요도 등)를 분석합니다.",
            "category": "관계 인텔리전스",
        },
        {
            "name": "일정 후보 추출 (Meeting Candidate Finder)",
            "description": "이메일 텍스트에서 회의나 약속으로 예상되는 시간대와 장소를 추출하여 캘린더 등록 초안을 생성합니다.",
            "category": "일정 관리",
        },
        {
            "name": "답장 어조 분석 및 교정 (Tone Analyzer & Editor)",
            "description": "작성 중인 답장의 어조를 분석하고, 수신자의 관계에 맞게 정중함이나 명확성을 교정해줍니다.",
            "category": "커뮤니케이션",
        },
    ]
