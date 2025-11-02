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
    _search_subsidies_internal,
    _get_json,
    API_BASE_URL,
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
    CORSMiddleware,
    allow_origins=["*"],  # GPTsからのアクセスを許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # プリフライトリクエストのキャッシュ時間
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーの詳細を返す"""
    logger.error(f"Validation error: {exc.errors()}")
    body_str = exc.body.decode('utf-8', errors='ignore') if exc.body else None
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": body_str
        }
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
        # バリデーション
        if not isinstance(keyword, str) or not keyword.strip() or not (2 <= len(keyword.strip()) <= 255):
            raise HTTPException(status_code=400, detail="keyword は2〜255文字の非空文字列で指定してください")
        if acceptance not in (0, 1):
            raise HTTPException(status_code=400, detail="acceptance は 0 または 1 を指定してください")
        allowed_sorts = {"created_date", "acceptance_start_datetime", "acceptance_end_datetime"}
        if sort not in allowed_sorts:
            raise HTTPException(status_code=400, detail="sort は created_date / acceptance_start_datetime / acceptance_end_datetime から選択してください")
        if str(order).upper() not in {"ASC", "DESC"}:
            raise HTTPException(status_code=400, detail="order は ASC または DESC を指定してください")
        
        result = await _search_subsidies_internal(
            keyword=keyword,
            use_purpose=use_purpose,
            industry=industry,
            target_number_of_employees=target_number_of_employees,
            target_area_search=target_area_search,
            sort=sort,
            order=str(order).upper(),
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
        if not isinstance(subsidy_id, str) or not subsidy_id.strip():
            raise HTTPException(status_code=400, detail="subsidy_id は非空の文字列で指定してください")
        
        url = f"{API_BASE_URL}/subsidies/id/{subsidy_id}"
        result = await _get_json(url)
        if "error" in result:
            if result["error"].startswith("HTTPエラー: 404"):
                raise HTTPException(status_code=404, detail=f"補助金ID '{subsidy_id}' が見つかりません")
            raise HTTPException(status_code=500, detail=result["error"])
        
        # レスポンスを整形
        if isinstance(result, dict):
            data_result = result.get("result", result)
            if isinstance(data_result, list) and len(data_result) > 0:
                result = data_result[0]
            elif isinstance(data_result, dict):
                result = data_result
            else:
                # より詳細なエラーメッセージ
                logger.error(f"予期しないレスポンス形式: result={result}, type={type(result)}")
                raise HTTPException(status_code=500, detail=f"予期しないレスポンス形式: {type(data_result).__name__}")
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
        logger.info("get_subsidy_overview_api called with output_format=%s", output_format)
        
        # デフォルトキーワードで検索して統計を計算
        try:
            subsidies = await _search_subsidies_internal()
            logger.info("_search_subsidies_internal returned: type=%s, keys=%s", type(subsidies).__name__, list(subsidies.keys()) if isinstance(subsidies, dict) else "N/A")
        except Exception as e:
            logger.error("Error calling _search_subsidies_internal: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"検索API呼び出しエラー: {str(e)}")
        
        if "error" in subsidies:
            logger.error("Search returned error: %s", subsidies.get("error"))
            raise HTTPException(status_code=500, detail=subsidies.get("error", "検索エラー"))
        
        # レスポンス形式を確認
        if not isinstance(subsidies, dict):
            logger.error("Unexpected response type: %s, value=%s", type(subsidies).__name__, str(subsidies)[:200])
            raise HTTPException(status_code=500, detail=f"予期しないレスポンス形式: 辞書型ではありません (type: {type(subsidies).__name__})")
        
        # 簡易的な統計情報を返す
        try:
            result = {
                "total_count": subsidies.get("total_count", 0),
                "subsidies_count": len(subsidies.get("subsidies", [])),
                "output_format": output_format,
                "note": "詳細な統計機能は準備中です。現在は検索結果の件数のみを返します。"
            }
            logger.info("Returning result: %s", result)
            return result
        except Exception as e:
            logger.error("Error creating result: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"結果生成エラー: {str(e)}")
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
        # 簡易実装（ファイル読み込みは実装していません）
        raise HTTPException(status_code=501, detail="get_file_content機能は準備中です")
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

