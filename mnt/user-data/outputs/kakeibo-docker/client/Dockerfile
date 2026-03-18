# 軽量なnginxイメージでPWAを配信
FROM nginx:alpine

# nginxの設定（SPAのルーティングとgzip圧縮）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# フロントエンドファイルをコピー
COPY index.html /usr/share/nginx/html/
COPY manifest.json /usr/share/nginx/html/
COPY sw.js /usr/share/nginx/html/

EXPOSE 80
