# -*- coding: utf-8 -*-
def check_spider_pipeline(process_item_func):
  def wrapper(self, item, spider):
    class_name = self.__class__.__name__
    if spider.ignored_pipelines and class_name in spider.ignored_pipelines:
      print('pipeline ignored: ', class_name)
      return item
    else:
      print('executing pipeline: ', class_name)
      return process_item_func(self, item, spider)
  return wrapper

def check_exit_condition(parse_func):
  def wrapper(self, response):
    print('[CRAWLED COUNT]', self.crawled_cnt, 'self.max_crawl_cnt ', self.max_crawl_cnt)
    if (not self.is_single_page_mode) and self.crawled_cnt >= self.max_crawl_cnt:
      self.log('reached max crawl count, will stop crawling')
      return
    print('[MIN CRAWLED DATE]', self.min_crawled_date, 'self.since_date ', self.since_date)
    if self.since_date and self.min_crawled_date:
      if self.min_crawled_date < self.since_date:
        self.log('crawled article is earlier than since date %s, will stop crawling' % self.since_date)
        return
    return parse_func(self, response)
  return wrapper
