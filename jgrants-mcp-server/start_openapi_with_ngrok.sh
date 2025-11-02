#!/usr/bin/env bash
# ngrokとOpenAPIサーバーを一緒に起動するスクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PORT=8001

# 既存のngrokプロセスを停止
echo "既存のngrokプロセスを確認中..."
pkill -f "ngrok http $PORT" 2>/dev/null
sleep 1

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

echo "=========================================="
echo "ngrokとOpenAPIサーバーを起動します"
echo "=========================================="
echo ""

# ngrokをバックグラウンドで起動
echo "ngrokを起動中..."
ngrok http $PORT > /tmp/ngrok_output.log 2>&1 &
NGROK_PID=$!
sleep 3

# ngrokのURLを取得
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  ngrokのURLを取得できませんでした"
    echo "手動で確認してください: http://127.0.0.1:4040"
    NGROK_URL="https://your-ngrok-url.ngrok-free.app"
else
    echo "✅ ngrok URL: $NGROK_URL"
fi

# 環境変数を設定してサーバーを起動
export SERVER_URL="$NGROK_URL"
export PORT=$PORT

echo ""
echo "OpenAPIサーバーを起動中..."
echo "OpenAPI JSON URL: $NGROK_URL/openapi.json"
echo ""
echo "GPTsのActions機能で使用するURL:"
echo "  $NGROK_URL/openapi.json"
echo ""
echo "停止するには Ctrl+C を押してください"
echo "=========================================="
echo ""

# Ctrl+Cをキャッチしてクリーンアップ
trap "kill $NGROK_PID 2>/dev/null; exit" INT TERM

# サーバーを起動
python -m jgrants_mcp_server.openapi_server

