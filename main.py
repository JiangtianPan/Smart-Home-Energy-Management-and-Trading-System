import uvicorn
from fastapi import FastAPI
from agents.facilitating_agent import FacilitatingAgent
from config import settings
from utils.logger import logger
from api.agent_routes import router as agent_router
from utils.error_handler import add_error_handlers

app = FastAPI(title="Facilitating Agent API")
app.include_router(agent_router)
add_error_handlers(app)

@app.on_event("startup")
async def startup():
    facilitator = FacilitatingAgent(settings.FACILITATOR_JID, settings.FACILITATOR_PASSWORD)
    await facilitator.start()
    app.state.facilitator = facilitator
    logger.info("Facilitating Agent started.")

@app.on_event("shutdown")
async def shutdown():
    facilitator = app.state.facilitator
    await facilitator.stop()
    logger.info("Facilitating Agent stopped.")

if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
