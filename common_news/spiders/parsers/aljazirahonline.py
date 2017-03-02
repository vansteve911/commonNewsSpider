import re
import traceback
from datetime import datetime
import dateparser
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class AljazirahOnlineSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('div.view-content div.views-row h2 a').xpath('@href').extract()

  def parse_next_page_url(self, response):
    return None

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('h2.mb10::text').extract_first() or response.css('div.mb10.mt10 h2::text').extract_first()
      item['author'] = response.css('.gal-pub div.field-item::text').extract_first() or ''
      date_str = response.css('span.gal-pub').re(r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}')
      date_str = date_str and date_str[0] or ''
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int(dateparser.parse(date_str).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or ''
      item['abstract'] = abstract.replace('\n', '')
      item['content_type'] = 0
      item['url'] = ''
      # whether is normal news or gallery news
      gallery_selector = response.css('div.news_node_image_gallery')
      if gallery_selector:
        item['content'], item['img'] = strip_html_imgs(gallery_selector)
      else:
        content_selector = response.css('div.lv3newsbody')
        thumbnail_selector = response.css('div.news_node_image img')
        content, item['img'] = strip_html_imgs(content_selector, thumbnail_selector)
        # get video ids
        html, item['video'] = extract_content_videos(content)
        if item['video']:
          item['content_type'] = 1
        else:
          item['content_type'] = 0
        # format html
        html = re.sub(r'\s+',' ',strip_html_attrs(html))
        html = html.replace('<br>', '</p><p>')
        item['content'] = html
      if not item['content']:
        raise Error('empty content in gallery page!')
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    return None

