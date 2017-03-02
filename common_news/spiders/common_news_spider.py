# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import datetime, timedelta
from ..items import CommonNewsItem
from scrapy.spiders import CrawlSpider
from ..common.config import SpiderSeeds
from ..common.utils import get_url_host, load_lines_in_file, format_url

from .parser_factory import parser_factory
from ..seed_manager import SeedManager
from ..decorators.checkers import check_exit_condition

class CommonNewsSpider(CrawlSpider):

  name = 'common_news'
  max_crawl_cnt = 200
  ignored_pipelines = None
  since_date = None
  seed = None

  def __init__(self,
               seed_name = None,
               start_urls_file = None,
               ignored_pipelines = None,
               max_crawl_cnt = None,
               max_day_before = None,
               *args,
               **kwargs):
    super(CommonNewsSpider, self).__init__(*args, **kwargs)
    if start_urls_file:
      self.is_single_page_mode = True
      start_urls = load_lines_in_file(start_urls_file)
      if not start_urls:
        raise Exception('error loading lines in file %s' % start_urls_file)
        return
      self.log('running in single page mode, load start urls: %s' % start_urls)
      self.start_urls = start_urls
      # self.seed = None
    else:
      seed = SeedManager().get_seed_by_name(seed_name)
      if not seed or not seed.get('url'):
        raise Exception('invalid url in seed %s' % seed_name)
      self.is_single_page_mode = False
      self.start_urls = [seed.get('url')]
      self.seed = seed
      self.host = get_url_host(seed.get('url'))
      # init global parser
      self.parser = parser_factory(seed_name)

    if ignored_pipelines:
      self.ignored_pipelines = ignored_pipelines.split(',') 
      self.log('custom ignore pipelines: %s' % self.ignored_pipelines)
    self.crawled_cnt = 0
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
    self.log('initialized spider, seed name: %s' % seed_name)

  @check_exit_condition
  def parse(self, response):
    # single page mode:
    if self.is_single_page_mode:
      yield next(self.parse_item(response))
      return
    # 
    found_list_page, next_search_links = self.parser.search_list_page(response)
    if not found_list_page:
      if not next_search_links:
        print('unable to search list page, next page uri is none')
        return
      print('current page is not list page, next page links: ', next_search_links)
      for link in next_search_links:
        yield scrapy.Request(self.host + link, callback = self.parse)
      return
    else:
      print('current page is list page: ', response.url) # TODO for test
    # 
    for article_url in self.parser.parse_article_urls(response):
      self.log('crawling url: %s' % article_url)
      yield scrapy.Request(self.host + article_url, callback=self.parse_item, dont_filter=True)
    next_page_url = self.parser.parse_next_page_url(response)
    if next_page_url:
      yield scrapy.Request(self.host + next_page_url, callback=self.parse)

  @check_exit_condition
  def parse_item(self, response):
    if self.is_single_page_mode:
      # get parser
      seed_prefix = SeedManager().search_seed_name_prefix(response.url)
      self.log('<single mode> find seed prefix[%s] from url [%s]' % (seed_prefix, response.url))
      parser =  parser_factory(seed_prefix + '_')
      category_url = format_url(parser.parse_category_url(response), sort_query_keys=True, strip_encoded_query=True)
      if category_url:
        seed = SeedManager().get_seed_by_url(category_url)
        if seed:
          self.log('<single mode> get seed by category url: %s' % seed)
        else:
          self.log('article has no matching seed, category url: %s' % category_url)
          return
      else:
        raise Exception('unable to get category url')
    else:
      # normal mode
      parser = self.parser
      seed = self.seed
    extra_info = {
        'scr': seed.get('id'),
        'cid': seed.get('cid'),
        'media_id': seed.get('media_id')
    }
    self.log('parsing %s, extra_info: %s' % (response.url, extra_info))
    item = parser.parse_article_item(response, extra_info)
    if item:
      self.crawled_cnt += 1
      self.log('crawled %d articles' % self.crawled_cnt)
      item_date = item.get('release_time') and datetime.fromtimestamp(item.get('release_time')/1000)
      if item_date and item_date < self.min_crawled_date:
        self.min_crawled_date = item_date
      self.log('current min crawled date: %s' % self.min_crawled_date)
      yield item
