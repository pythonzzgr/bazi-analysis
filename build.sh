#!/usr/bin/env bash
set -e

echo "=== 프론트엔드 빌드 ==="
cd frontend
npm run build
cd ..

echo "=== 백엔드로 복사 ==="
rm -rf backend/static
cp -r frontend/out backend/static

echo "=== 완료! ==="
echo "실행: cd backend && python main.py"
