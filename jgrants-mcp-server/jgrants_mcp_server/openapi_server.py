"""
JグランツMCPサーバー - OpenAPI仕様でHTTP REST APIとして提供
GPTsのActions機能で使用するためのOpenAPI仕様を提供します。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from jgrants_mcp_server.core import (
    search_subsidies,
    get_subsidy_detail,
    get_subsidy_overview,
    get_file_content
)

app = FastAPI(
    title="Jグランツ補助金検索API",
    description="デジタル庁Jグランツ（補助金電子申請システム）の公開APIをラップしたREST API。GPTsのActions機能で使用可能。",
    version="1.0.0",
    servers=[
        {
            "url": os.getenv("RENDER_EXTERNAL_URL", os.getenv("SERVER_URL", "http://localhost:8001")),
            "description": "本番環境" if os.getenv("RENDER_EXTERNAL_URL") else ("開発環境 (ngrok)" if os.getenv("SERVER_URL") else "ローカル開発環境")
        },
    ],
)

# CORS設定（GPTsからのアクセスを許可）
app.add_middleware(

            "detail": exc.errors(),
            "body": body_str
        }
    )

    CORSMiddleware,
    allow_origins=["*"],  # GPTsからのアクセスを許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # プリフライトリクエストのキャッシュ時間
)


@app.get("/", tags=["Health"])
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "service": "Jグランツ補助金検索API",
        "version": "1.0.0"
    }


@app.get("/subsidies/search", tags=["補助金検索"])
async def search_subsidies_api(
    keyword: str = Query(..., description="検索キーワード（2文字以上必須）", min_length=2),
    use_purpose: Optional[str] = Query(None, description="利用目的"),
    industry: Optional[str] = Query(None, description="業種"),
    target_number_of_employees: Optional[str] = Query(None, description="従業員数制約"),
    target_area_search: Optional[str] = Query(None, description="対象地域"),
    sort: str = Query("acceptance_end_datetime", description="ソート順（created_date / acceptance_start_datetime / acceptance_end_datetime）"),
    order: str = Query("ASC", description="昇順/降順（ASC / DESC）"),
    acceptance: int = Query(1, description="受付状態（0: 全て / 1: 受付中のみ）")
):
    """
    補助金を検索します。

    キーワード、業種、地域、従業員数などで絞り込みが可能です。
    """
    try:
        result = await search_subsidies(
            keyword=keyword,
            use_purpose=use_purpose,
            industry=industry,
            target_number_of_employees=target_number_of_employees,
            target_area_search=target_area_search,
            sort=sort,
            order=order,
            acceptance=acceptance
        )
        # エラーオブジェクトが返された場合はHTTPExceptionを発生
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"検索エラー: {str(e)}"
        print(f"ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/subsidies/{subsidy_id}", tags=["補助金詳細"])
async def get_subsidy_detail_api(subsidy_id: str):
    """
    補助金の詳細情報を取得します。

    - **subsidy_id**: 補助金ID（18文字以下）
    """
    try:
        result = await get_subsidy_detail(subsidy_id=subsidy_id)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"詳細取得エラー: {str(e)}"
        print(f"ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/subsidies/overview", tags=["統計情報"])
async def get_subsidy_overview_api(
    output_format: str = Query("json", description="出力形式（json / csv）")
):
    """
    補助金の統計情報を取得します。

    締切期間別、金額規模別の集計を提供します。
    """
    try:
        result = await get_subsidy_overview(output_format=output_format)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"統計情報取得エラー: {str(e)}"
        print(f"ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/subsidies/{subsidy_id}/files/{filename}", tags=["ファイル内容"])
async def get_file_content_api(
    subsidy_id: str,
    filename: str,
    return_format: str = Query("markdown", description="返却形式（markdown / base64）")
):
    """
    保存済みの添付ファイルの内容を取得します。

    PDF、Word、Excel、PowerPoint、ZIPをMarkdownに自動変換します。
    """
    try:
        result = await get_file_content(
            subsidy_id=subsidy_id,
            filename=filename,
            return_format=return_format
        )
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"ファイル取得エラー: {str(e)}"
        print(f"ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/ping", tags=["Health"])
async def ping():
    """サーバーの疎通確認を行います。"""
    return {"status": "ok", "message": "pong"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

