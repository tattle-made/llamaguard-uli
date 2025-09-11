import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from service import ContentModerationService, ModerationRequest, ModerationResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Content Moderation API", version="0.0.1")

moderation_service = ContentModerationService()


@app.get("/")
def read_root():
    return {"message": "Content Moderation API", "version": "0.0.1"}


@app.post("/moderate", response_model=ModerationResponse)
def moderate_content(request: ModerationRequest):
    """
    Main endpoint for content moderation

    Returns:
    - should_moderate: boolean indicating if content should be moderated
    - reason: string explaining why the decision was made
    - flagged_words: list of words that triggered the decision
    - processing_time_ms: time taken to process the request
    """
    try:
        result = moderation_service.moderate_content(request.text)
        return JSONResponse(content=ModerationResponse(**result).model_dump(), status_code=result.get("status_code", 200))
    except Exception as e:
        logger.error(f"Error during moderation: {e}")
        error_body = ModerationResponse(
            meta={
                "response_time": 0.0,
                "flagged_words": [],
            },
            should_moderate=False,
            reason=None,
            status_code=500,
        ).model_dump()
        return JSONResponse(content=error_body, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
