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
SEED_LIST=`cat ${SPIDER_DIR}/resources/available_seeds_rss.txt | xargs`
echo "availble_seeds: $SEED_LIST"
for seed in ${SEED_LIST} ; do
  echo "[RSS_FETCH] start fetching seed: ${seed}"
  scrapy crawl arab_rss -a seed_name=${seed} -a max_day_before=1 --logfile="${LOG_DIR}/crawl_`date +%Y-%m-%d`_${seed}.log" &
  sleep 60
  echo "[RSS_FETCH] end fetching seed: ${seed}"
done

cd "${SPIDER_DIR}/script"
# python sys_spider.py >> "${LOG_DIR}/migrate_`date +%Y-%m-%d`.log" &