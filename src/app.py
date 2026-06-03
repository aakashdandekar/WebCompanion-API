from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis import Redis
from langchain.messages import AIMessage, HumanMessage
from src.core.redis import redis, getRedis
from src.auth.auth import get_current_user
from src.services.agents.agent import run_agent
from src.services.helpers import getSessionId

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis
    await app.state.redis.ping()

    yield
    await app.state.redis.aclose()

app = FastAPI(lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credintials=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post('/api/agent/invoke')
async def agent_invoke(
    query: str,
    current_user: str = Depends(get_current_user),
    cache: Redis = Depends(getRedis)
) -> dict:
    try:
        session_id = await cache.get(f"Session-{current_user}")
        if not session_id:
            session_id = getSessionId(current_user)
            activeSession = await redis.lrange("Active Sessions", 0, -1)

            if session_id not in activeSession:
                await redis.rpush("Active Sessions", session_id)
    
            await cache.set(f"Session-{current_user}", session_id)

        session_history = await cache.get(session_id, current_user)

        session_history = session_history if session_history else []
        response = await run_agent(query, session_history)

        session_history.append(HumanMessage(query))
        session_history.append(AIMessage(response))

        await cache.set(session_id, session_history, 86400)

        return {"message": response}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
@app.get('/api/agent/memory')
async def agent_memory(
    cache: Redis = Depends(getRedis)
) -> dict:
    try:
        return await cache.lrange("Active Sessions", 0, -1)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get('/api/agent/memory/me')
async def agent_memory_user(
    current_user: str = Depends(get_current_user),
    cache: Redis = Depends(getRedis)
) -> dict:
    try:
        session_id = await cache.get(f"Session-{current_user}")
        if not session_id:
            raise HTTPException(status_code=400, detail="User not found!")
        
        return await cache.get(session_id)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
@app.get('/api/agent/active-session')
async def get_active_sessions(
    cache: Redis = Depends(getRedis)
) -> list[str]:
    try:
        activeSessions = await cache.lrange("Active Sessions", 0, -1)
        return { "message": activeSessions }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
@app.delete('/api/agent/delete')
async def delete_agent_session(
    current_user: str = Depends(get_current_user),
    cache: Redis = Depends(getRedis)
):
    try:
        session_id = await cache.get(f"Session-{current_user}")
        if not session_id:
            return { "message": "Agent session does not exists!" }
        
        await cache.delete(f"Session-{current_user}")

        await redis.lrem("Active Sessions", 0, session_id)
        return { "message": "Agent Session Deleted!" }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error")