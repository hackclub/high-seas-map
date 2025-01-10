FROM python:3.12-bookworm

WORKDIR /usr/src/app

COPY requirements.txt package.json package-lock.json index.html postcss.config.js tailwind.config.js tsconfig.json vite.config.ts ./

RUN apt update
RUN apt install -y libcairo2 libcairo2-dev python3-cairo nodejs npm

RUN pip install --no-cache-dir -r requirements.txt
RUN npm install

RUN --mount=type=bind,source=src,target=/usr/src/app/src \
  npm run build

CMD ["./start.sh"]