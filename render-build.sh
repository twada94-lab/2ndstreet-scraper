#!/usr/bin/env bash
set -eux

echo "🚀 Installing Chrome in Render build..."

apt-get update
apt-get install -y wget gnupg unzip curl

# ✅ Google Chrome の公式キーとリポジトリを追加
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update

# ✅ Chrome をインストール
apt-get install -y google-chrome-stable

# ✅ いくつかの名前でシンボリックリンクを張る（互換性のため）
ln -sf /usr/bin/google-chrome-stable /usr/bin/google-chrome
ln -sf /usr/bin/google-chrome-stable /usr/bin/chromium-browser
ln -sf /usr/bin/google-chrome-stable /usr/bin/chromium

echo "✅ Chrome installation complete."
google-chrome --version || echo "⚠️ Chrome not found!"
