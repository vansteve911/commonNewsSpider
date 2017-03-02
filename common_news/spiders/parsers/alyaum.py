import re
import traceback
from datetime import datetime, timedelta
import dateparser
from ...items import CommonNewsItem
from ...common.utils import strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class AlyaumSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('div.content-block.main.right div.block-content div.article-big a').xpath('@href').extract()

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
      item['title'] = response.css('div.article-title h2::text').extract_first()
      item['author'] = response.css('div.author div.a-content span a::text').extract_first() or ''
      # date_str = date_str and date_str[0] or ''
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        date_str = response.css('div.author div.a-content span.meta::text').extract_first()
        date_parts = date_str.split(',')
        dt = dateparser.parse('%s, %s' % (date_parts[0], date_parts[1]))
        hours = int(re.search('\d+',date_parts[2]).group(0))
        if re.search('ص',date_parts[2]):
          hours += 12
        dt = dt + timedelta(hours=hours)
        item['release_time'] = int(dt.timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      item['abstract'] = response.css('div.article-title h4::text').extract_first() or ''
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('div.block-content div.paragraph-row div.column9')
      thumbnail_selector = response.css('div.wp-caption img.article_img1st')
      content, item['img'] = strip_html_imgs(content_selector, thumbnail_selector)
      # get video ids
      html, item['video'] = extract_content_videos(content)
      if item['video']:
        item['content_type'] = 1
      else:
        item['content_type'] = 0
      # format html
      html = re.sub(r'\s+',' ',strip_html_attrs(html))
      item['content'] = html
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    return response.css('ul.the-menu li a.active').xpath('@href').extract_first()

