# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import datetime, timedelta
import dateparser
from ..items import CommonNewsItem
from scrapy.spiders import CrawlSpider
from ..common.config import SpiderSeeds
from ..common.utils import get_url_host, load_lines_in_file, format_url

from .parser_factory import parser_factory
from ..seed_manager import SeedManager
from ..decorators.checkers import check_exit_condition

class CommonRssSpider(CrawlSpider):

  max_crawl_cnt = 200  # TODO
  name = 'arab_rss'
  ignored_pipelines = None
  since_date = None
  is_single_page_mode = False

  def __init__(self, 
      seed_name = 'almowaten_tech', 
      ignored_pipelines = None,
      max_crawl_cnt = None,
      max_day_before = None,
      *args, 
      **kwargs):
    super(CommonRssSpider, self).__init__(*args, **kwargs)
    self.crawled_cnt = 0
    seed = SeedManager().get_seed_by_name(seed_name)
    self.seed = seed
    rss_url = seed.get('rss')
    self.host = get_url_host(rss_url)
    if not rss_url or not self.host:
      raise Exception('invalid RSS seed: %s' % seed_name)
    self.start_urls = [rss_url]
    self.parser = parser_factory(seed_name)
    if ignored_pipelines:
      self.ignored_pipelines = ignored_pipelines.split(',') 
      self.log('custom ignore pipelines: %s' % self.ignored_pipelines)
    if max_crawl_cnt:
      try:
        self.max_crawl_cnt = int(max_crawl_cnt)
        self.log('custom max crawl cnt: %s' %  max_crawl_cnt)
      except:
        self.log('parse max crawl cnt failed!', max_crawl_cnt)
    self.min_crawled_date = datetime.now()
    if max_day_before:
      try:
        self.since_date = self.min_crawled_date - timedelta(days = int(max_day_before))
        self.log('custom since date: %s' %  self.since_date)
      except:
        self.log('parse max_day_before failed!', max_day_before)
        self.since_date = None
    self.log('initialized RSS spider, seed name: %s' % seed_name)

  def parse(self, response):
    for item_sel in response.xpath('/rss/channel/item'):
      yield self.__parse_rss_item(item_sel)
    
  def __parse_rss_item(self, item_sel):
    article_url = item_sel.xpath('link/text()').extract_first()
    request = scrapy.Request(article_url, callback=self.parse_item)
    date_str = item_sel.xpath('pubDate/text()').extract_first()
    description = item_sel.xpath('description/text()').extract_first()
    if date_str:
      try:
        request.meta['release_time'] = int(dateparser.parse(date_str).timestamp() * 1000)
      except Exception as e:
        print('failed to parse time: %s' % date_str, e)
    request.meta.update({
      'extra_info': {
        'scr': self.seed.get('id'),
        'cid': self.seed.get('cid'),
        'media_id': self.seed.get('media_id'),
        'abstract': description
      }
    })
    return request

  @check_exit_condition
  def parse_item(self, response):
    extra_info = response.meta.get('extra_info')
    if not extra_info.get('scr'):
      category_url = format_url(parser.parse_category_url(response), sort_query_keys=True, strip_encoded_query=True)
      if category_url:
        seed = SeedManager().get_seed_by_url(category_url)
        if seed:
          print('get seed by category url: ', seed)
          extra_info.update({
            'scr': seed.get('id'),
            'cid': seed.get('cid'),
            'media_id': seed.get('media_id'),
          })
        else:
          self.log('article has no matching seed, category url: %s' % category_url)
          return
      else:
        raise Exception('unable to get category url')
    self.log('parsing %s, extra_info: %s' % (response.url, extra_info))
    item = self.parser.parse_article_item(response, extra_info)
    if item:
      self.crawled_cnt += 1
      self.log('crawled %d articles' % self.crawled_cnt)
      item_date = item.get('release_time') and datetime.fromtimestamp(item.get('release_time')/1000)
      if item_date and item_date < self.min_crawled_date:
        self.min_crawled_date = item_date
      self.log('current min crawled date: %s' % self.min_crawled_date)
      yield item
