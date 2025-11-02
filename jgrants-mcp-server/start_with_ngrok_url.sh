#!/usr/bin/env bash
# ngrok URLを自動取得してOpenAPIサーバーを起動するスクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 仮想環境を有効化
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

source venv/bin/activate

# FastAPIがインストールされていない場合はインストール
if ! python -c "import fastapi" 2>/dev/null; then
    echo "FastAPIをインストールしています..."
    pip install fastapi uvicorn
fi

# ngrokのURLを取得
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); tunnels = data.get('tunnels', []); print(tunnels[0]['public_url'] if tunnels and 'public_url' in tunnels[0] else '')" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  警告: ngrokのURLを取得できませんでした"
    echo ""
    echo "ngrokが起動しているか確認してください:"
    echo "  別のターミナルで: ngrok http 8001"
    echo ""
    echo "ngrokが起動したら、このスクリプトを再実行してください。"
    exit 1
fi

echo "=========================================="
echo "JグランツOpenAPIサーバーを起動しています..."
echo "ngrok URL: $NGROK_URL"
echo "OpenAPI JSON: $NGROK_URL/openapi.json"
echo ""
echo "GPTsのActions機能で使用するURL:"
echo "  $NGROK_URL/openapi.json"
echo ""
echo "停止するには Ctrl+C を押してください"
echo "=========================================="
echo ""

# 環境変数を設定してサーバーを起動
export SERVER_URL="$NGROK_URL"
python -m jgrants_mcp_server.openapi_server
