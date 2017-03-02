#!/bin/bash
SPIDER_DIR="/root/commonNews/commonNewsSpider"
LOG_DIR="/var/log/commonNewsSpider"

if [ $# -eq 1 ] ; then
  ENV=$1
  if [ $1 = "online" ] ; then
    export SCRAPY_SETTINGS_MODULE="common_news.settings.settings_online"
  else:
    export SCRAPY_SETTINGS_MODULE="common_news.settings.settings_test"
  fi
else:
  echo "usage: news_fetch.sh <test|online>"
  exit 1
fi

cd "${SPIDER_DIR}/common_news"
SEED_LIST=`cat ${SPIDER_DIR}/resources/available_seeds.txt | xargs`
echo "availble_seeds: $SEED_LIST"
for seed in ${SEED_LIST} ; do
  echo "[NEWS_FETCH] start fetching seed: ${seed}"
  scrapy crawl common_news -a max_day_before=1 -a seed_name=${seed} --logfile="${LOG_DIR}/crawl_`date +%Y-%m-%d`_${seed}.log" &
  sleep 60
  echo "[NEWS_FETCH] end fetching seed: ${seed}"
done