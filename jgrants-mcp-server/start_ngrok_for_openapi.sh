#!/usr/bin/env bash
# ngrokでOpenAPIサーバー（ポート8001）を公開するスクリプト

echo "=========================================="
echo "ngrokでOpenAPIサーバーを公開します"
echo "対象ポート: 8001"
echo ""
echo "⚠️  注意: このスクリプトはngrokプロセスを実行します"
echo "停止するには Ctrl+C を押してください"
echo "=========================================="
echo ""

# サーバーが起動しているか確認
if ! curl -s http://localhost:8001/ping > /dev/null 2>&1; then
    echo "⚠️  警告: OpenAPIサーバーが起動していない可能性があります"
    echo "先に以下のコマンドでサーバーを起動してください:"
    echo "  cd jgrants-mcp-server"
    echo "  ./start_openapi_server.sh"
    echo ""
    read -p "それでも続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ngrokがインストールされているか確認
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrokがインストールされていません"
    echo ""
    echo "インストール方法:"
    echo "  # macOS (Homebrew)"
    echo "  brew install ngrok/ngrok/ngrok"
    echo ""
    echo "  # または公式サイトからダウンロード"
    echo "  https://ngrok.com/download"
    exit 1
fi

# ngrokでポート8001を公開
echo "ngrokを起動しています..."
echo "公開URLが表示されたら、以下のURLをGPTsのActions機能で使用してください:"
echo "  https://xxxx-xxx-xxx.ngrok-free.app/openapi.json"
echo ""
echo "=========================================="
echo ""

ngrok http 8001

