import re
import traceback
import random
from datetime import datetime
import dateparser
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, filter_html_tags, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class BabSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('div#main-col div.list-posts-cat div.item-right h3 a').xpath('@href').extract()
    
  def parse_next_page_url(self, response):
    return response.css('div#main-col ul.page-numbers a.next').xpath('@href').extract_first()

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('article.post-content header.clearfix h3.title-post::text').extract_first()
      item['author'] = ''
      date_str = response.css('article.post-content div.header-bottom p.kp-metadata.style-2 span::text').extract()
      if date_str and len(date_str) > 1:
        date_str = date_str[1]
      else:
        date_str = ''
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int((dateparser.parse(date_str).timestamp()*1000))
        # add random time offset (from 8.am to 8.pm)
        item['release_time'] += random.randint(28800,108000)*1000
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or ''
      item['abstract'] = filter_html_tags(abstract, [])
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('article.post-content div.entry-content')
      thumbnail_selector = response.css('article.post-content div.kp-thumb img')
      content, item['img'] = strip_html_imgs(content_selector, thumbnail_selector, host = 'http://www.bab.com')
      # get video ids
      html, item['video'] = extract_content_videos(content)
      if item['video']:
        item['content_type'] = 1
      else:
        item['content_type'] = 0
      # format html
      html = re.sub(r'\s+',' ',strip_html_attrs(html))
      html = re.sub('(<br>\s*){1,}', '</p><p>', html)
      html = re.sub(r'</?[^p!][^>]*>','',html)
      item['content'] = html
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    link_sels = response.css('div#main-col.pull-right ul.breadcrumb li a').xpath('@href').extract()
    if link_sels and len(link_sels) > 0:
      return 'http://www.bab.com' + link_sels[1]
