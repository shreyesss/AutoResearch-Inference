"""Narrow flush route, called by root only after strict all-engine/router drain."""
from fastapi import APIRouter, Request
router=APIRouter()
@router.post('/c25_live/flush')
async def flush(request:Request):
    body=await request.json()
    if set(body)!={'run_id','arm','nonce'} or body['arm'] not in ('A','B'):
        raise ValueError('invalid flush identity')
    result=await request.app.state.engine_client.collective_rpc(
        'c25_live_timing_flush',timeout=30,kwargs=body)
    return {'rpc_return':result,'all_rank_files_required':True}
def attach_router(app):
    app.include_router(router)
