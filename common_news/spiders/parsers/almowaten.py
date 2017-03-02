import re
import traceback
from datetime import datetime, timedelta
from ...items import CommonNewsItem
from scrapy.spiders import CrawlSpider
from ...common.config import SpiderSeeds
from ...common.utils import parse_arabic_date, strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser
from ...seed_manager import SeedManager

import json

SPACE_PATTERN = re.compile('(\n|\s)+')
AUTHOR_PATTERN = re.compile(r'\-([^\-]+)\-')


class AlmowatenSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('#content.content .post-content').xpath('a/@href').extract()

  def parse_next_page_url(self, response):
    return response.xpath(
        '//div[@id="content"]/div[@class="pagination"]//a[@class="pagenavi-next"]/@href').extract_first()

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info['scr']  # seed source id
      item['cid'] = extra_info['cid']  # cid
      item['media'] = extra_info['media_id']  # media: news_medias
      item['title'] = response.css('#post-header-bd h1::text').extract_first()
      item['author'] = self.__parse_author(response)
      date_str = response.css(
          '#post-header-bd div.meta-info div.post-date-bd span::text').extract_first()
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        # post_time = self.__parse_date(response)
        date_str = response.xpath('//head/meta[@property="article:published_time"]/@content').extract_first()
        item['release_time'] = int((datetime.strptime(date_str,'%Y-%m-%dT%H:%M:%SZ')).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      item['abstract'] = extra_info.get('abstract') or ''  # item['title']
      item['url'] = ''
      content_selector = response.css('#content div.post-content-bd')
      content, item['img'] = strip_html_imgs(content_selector)
      # get video ids
      html, item['video'] = extract_content_videos(content)
      if item['video']:
        item['content_type'] = 1
      else:
        item['content_type'] = 0
      # format html
      html = re.sub(r'\s+',' ',strip_html_attrs(html))
      # html = re.sub(r'</?span[^>]*>','',html)
      html = re.sub(r'</?[^p!b][^>]*>','',html)
      item['content'] = html

    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['release_time'] = None
    return item

  def __parse_author(self, response):
    full_author = response.css(
        '#content div.post-content-bd p span::text').extract_first() or ''  # author
    author = ''
    if full_author:
      match = re.search(AUTHOR_PATTERN, full_author)
      if match:
        author = match.group(1)
    return author

  def __parse_date(self, response):
    try:
      date_str = response.xpath(
          '//div[@class="post-date-bd"]/span/text()').extract_first()
      print('date_str', date_str)
      date_obj = parse_arabic_date(date_str)
      time_sels = response.xpath('//div[@class="meta-info"]/text()').extract()
      iter = filter(
          None, map(lambda x: re.sub(SPACE_PATTERN, '', x), time_sels))
      time_str = next(iter) or ''
      time_obj = parse_arabic_date(time_str)
      ret = date_obj + timedelta(hours=time_obj.hour, minutes=time_obj.minute)
      print('parsed date: ', ret)
      return ret
    except Exception as e:
      print('failed to parse date', e)
      traceback.print_exc()

  def parse_category_url(self, response):
    return response.css(
        '#post-header-bd .vbreadcrumb').xpath('a[@itemprop]/@href').re('http://[^/]+/category/[^/]+/?')[0]
