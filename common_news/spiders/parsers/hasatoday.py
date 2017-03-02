import re
import traceback
from datetime import datetime
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class HasatodaySiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None
  
  def parse_article_urls(self, response):
    return list(map(lambda x:x.replace('http://www.hasatoday.com/', ''), response.css('#category-posts h2.the-title').xpath('a/@href').extract()))

  def parse_next_page_url(self, response):
    return response.css('#content ul.page-numbers a.next.page-numbers').xpath('@href').extract_first().replace()

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('#post-content h1.entry-title::text').extract_first()
      item['author'] = response.css('#post-content div.pf-content span[style="color: #0000ff;"] strong::text').extract_first() or ''
      date_str = response.css('#post-content li.calendar time.entry-date.updated').xpath('@datetime').extract_first()
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int((datetime.strptime(date_str,'%Y-%m-%dT%H:%M:%S+00:00')).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or response.css('#post-content h2.small-title::text').extract_first() or ''
      item['abstract'] = abstract.replace('\n', '')
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('#post-content div.pf-content')
      thumbnail_selector = response.css('#post-content div.post-image.thumbnail')
      if thumbnail_selector:
        print('found thumbnail: %s' % thumbnail_selector.extract_first())
      content, item['img'] = strip_html_imgs(
        content_selector, thumbnail_selector, custom_filter_xpath='descendant::p[not(contains(@style,"display"))]|descendant::div//img[not(contains(@alt,"PrintFriendly and PDF"))]|text()')
      # extract videos
      html, item['video'] = extract_content_videos(content)
      if item['video']:
        item['content_type'] = 1
      else:
        item['content_type'] = 0
      # format html
      html = re.sub(r'\s+',' ',strip_html_attrs(html))
      html = re.sub(r'</?[^p!][^>]*>','',html)
      item['content'] = html
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    return response.css('div#crumbs').xpath('div[@itemscope]').re('http://[^/]+/category/[^"]+/?')[0]

