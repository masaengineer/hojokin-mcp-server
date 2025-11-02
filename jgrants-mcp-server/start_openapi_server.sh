#!/usr/bin/env bash
# JグランツOpenAPIサーバー起動スクリプト（GPTs Actions用）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 仮想環境が存在しない場合は作成
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境を有効化
source venv/bin/activate

# FastAPIがインストールされているか確認
if ! python -c "import fastapi" 2>/dev/null; then
    echo "FastAPIをインストールしています..."
    pip install fastapi uvicorn
fi

# ポート番号を取得（デフォルト: 8001）
PORT=${1:-8001}

echo "=========================================="
echo "JグランツOpenAPIサーバーを起動しています..."
echo "ローカルエンドポイント: http://localhost:$PORT"
echo "OpenAPI仕様: http://localhost:$PORT/docs"
echo "OpenAPI JSON: http://localhost:$PORT/openapi.json"
echo ""
echo "GPTsのActions機能で使用する場合:"
echo "  - Schema URL: http://localhost:$PORT/openapi.json"
echo "  - または ngrok で公開: ngrok http $PORT"
echo ""
echo "停止するには Ctrl+C を押してください"
echo "=========================================="
echo ""

python -m jgrants_mcp_server.openapi_server

