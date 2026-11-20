"""Optional FastAPI adapter for RagLeap; mount router in the RagLeap application."""
from daily_signal_service import run_daily_scan, get_dashboard_data, format_report
try:
    from fastapi import APIRouter, HTTPException
    router=APIRouter(prefix="/api/daily-signal",tags=["daily-signal"])
    @router.get("/latest")
    def latest(limit: int=100):
        try: return get_dashboard_data(limit=max(1,min(limit,1000)))
        except Exception as exc: raise HTTPException(status_code=500,detail=str(exc))
    @router.post("/scan")
    def scan():
        try:
            result=run_daily_scan()
            return {"counts":result["counts"],"report":format_report(result),"results":result["results"],"errors":result["errors"]}
        except Exception as exc: raise HTTPException(status_code=500,detail=str(exc))
except ImportError:
    router=None
