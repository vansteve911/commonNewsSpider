import re
import traceback
from datetime import datetime
import dateparser
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class AlbawabaSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('div.views-row span.field-content a').xpath('@href').extract()

  def parse_next_page_url(self, response):
    category_id_in_first_page = response.xpath('head/script').re('search_term":"(\d+)"')
    if category_id_in_first_page:
      category_id_in_first_page = category_id_in_first_page[0]
      return '/morelistings?&page=1&type=%s&lang=ar' % category_id_in_first_page
    else:
      m = re.search(r'morelistings\?&page=(\d+)', response.url)
      if m:
        curr_page_num = m.group(1)
        next_page_num = str(int(curr_page_num) + 1)
        return response.url.replace('http://www.albawaba.com', '').replace(curr_page_num, next_page_num)

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('div#main h1.title::text').extract_first()
      item['author'] = ''
      date_str = response.xpath('head/meta[contains(@property,"article:published_time")]/@content').extract_first()
      # date_str = date_str and date_str[0] or ''
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int(dateparser.parse(date_str).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or ''
      item['abstract'] = abstract.replace('\n', '')
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('div.content.clearfix')
      content, item['img'] = strip_html_imgs(
          content_selector)
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
    link = response.css('div#breadcrumbs a.active').xpath('@href').re(r'^/ar/[^/]+$')
    if link:
      return 'http://www.albawaba.com%s' % link[0]

