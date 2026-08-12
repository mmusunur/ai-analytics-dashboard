"""
Data Router — CSV upload, sample data, and summary endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services import data_service

router = APIRouter()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV or Excel file and load it into memory."""
    fname = (file.filename or "").lower()
    if not fname.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    content = await file.read()
    try:
        if fname.endswith(".csv"):
            df = data_service.load_from_csv_bytes(content)
        else:
            df = data_service.load_from_excel_bytes(content)
        return JSONResponse({
            "message": f"✅ Uploaded '{file.filename}' successfully",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist()
        })
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {str(e)}")


@router.get("/sample")
async def get_sample_data(rows: int = 100):
    """Return sample data (first N rows) for preview."""
    df = data_service.get_or_generate()
    data = df.head(rows).fillna("").to_dict(orient="records")
    return JSONResponse({
        "data": data,
        "columns": df.columns.tolist(),
        "total_rows": len(df)
    })


@router.get("/summary")
async def get_summary():
    """Return statistical summary of the current dataset."""
    df = data_service.get_or_generate()
    summary = data_service.summarize(df)
    return JSONResponse(summary)


@router.delete("/reset")
async def reset_data():
    """Clear the in-memory dataset and reload sample data."""
    data_service.set_dataframe(None)
    return JSONResponse({"message": "Dataset reset to sample data"})
