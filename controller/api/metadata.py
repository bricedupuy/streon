"""
Metadata API endpoints
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
from pydantic import BaseModel

from core.metadata_service import metadata_service, MetadataUpdate

router = APIRouter()


class MetadataResponse(BaseModel):
    flow_id: str
    artist: str | None
    title: str | None
    album: str | None
    duration_ms: int | None
    source: str | None
    timestamp: str


class MetadataInjectRequest(BaseModel):
    artist: str | None = None
    title: str | None = None
    album: str | None = None
    duration_ms: int | None = None
    source: str | None = "manual"


@router.get("/metadata/{flow_id}", response_model=MetadataResponse | None)
async def get_current_metadata(flow_id: str):
    """
    Get current metadata for a Flow
    """
    metadata = metadata_service.get_current_metadata(flow_id)

    if not metadata:
        raise HTTPException(status_code=404, detail="No metadata available for this Flow")

    return MetadataResponse(
        flow_id=metadata.flow_id,
        artist=metadata.artist,
        title=metadata.title,
        album=metadata.album,
        duration_ms=metadata.duration_ms,
        source=metadata.source,
        timestamp=metadata.timestamp.isoformat()
    )


@router.get("/metadata/{flow_id}/history")
async def get_metadata_history(flow_id: str, limit: int = 10):
    """
    Get metadata history for a Flow
    """
    history = metadata_service.get_metadata_history(flow_id, limit)

    return {
        "flow_id": flow_id,
        "count": len(history),
        "history": [
            MetadataResponse(
                flow_id=m.flow_id,
                artist=m.artist,
                title=m.title,
                album=m.album,
                duration_ms=m.duration_ms,
                source=m.source,
                timestamp=m.timestamp.isoformat()
            ) for m in history
        ]
    }


@router.post("/metadata/{flow_id}/inject")
async def inject_metadata(flow_id: str, request: MetadataInjectRequest):
    """
    Manually inject metadata for a Flow (for testing or external sources)
    """
    await metadata_service.inject_metadata(flow_id, request.model_dump())

    return {
        "message": "Metadata injected successfully",
        "flow_id": flow_id,
        "metadata": request.model_dump()
    }


@router.websocket("/metadata/stream")
async def metadata_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metadata updates
    Clients will receive JSON messages for all metadata updates across all Flows
    """
    await websocket.accept()
    await metadata_service.register_websocket(websocket)

    try:
        # Keep connection alive and wait for disconnect
        while True:
            # Receive ping/pong or commands from client
            data = await websocket.receive_text()

            # Handle client commands (if any)
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        await metadata_service.unregister_websocket(websocket)
    except Exception as e:
        await metadata_service.unregister_websocket(websocket)
        raise


@router.get("/metadata")
async def get_all_metadata():
    """
    Get current metadata for all active Flows
    """
    all_metadata = {}

    for flow_id, handler in metadata_service.flow_handlers.items():
        metadata = handler.get_current_metadata()
        if metadata:
            all_metadata[flow_id] = MetadataResponse(
                flow_id=metadata.flow_id,
                artist=metadata.artist,
                title=metadata.title,
                album=metadata.album,
                duration_ms=metadata.duration_ms,
                source=metadata.source,
                timestamp=metadata.timestamp.isoformat()
            )

    return {
        "count": len(all_metadata),
        "flows": all_metadata
    }
