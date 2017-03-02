import re
from scrapy.selector import Selector, SelectorList
import traceback
from datetime import datetime
import dateparser
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class ElaphSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None
  
  def parse_article_urls(self, response):
    return list(map(lambda x:x.replace('http://elaph.com', ''), response.css('div#section-main-right div.subnews a.title').xpath('@href').extract()))

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
      item['title'] = response.css('div#article div.articlehead h1::text').extract_first().replace('\r\n', '')
      author = response.css('div#article div.articlehead span.author::text').extract_first() or ''
      item['author'] = author.replace('\r\n', '')
      date_str = '%s %s' % (response.xpath('head/meta[contains(@name,"publication_date")]/@content').extract_first(), response.css('div#article.bloc span.timestampUpdatedright').re_first('\d+:\d\d'))
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int((datetime.strptime(date_str,'%Y-%m-%d %H:%M')).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or response.css('div#article div.articlehead span.kicker::text').extract_first() or ''
      item['abstract'] = abstract.replace('\r\n', '')
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('div#articlebody')
      thumbnail_src = response.xpath('head/meta[@property = "og:image"]/@content').extract_first()
      thumbnail_selector = SelectorList([Selector(text = '<img src="%s">' % thumbnail_src)])
      content, item['img'] = strip_html_imgs(content_selector, thumbnail_selector)
      # extract videos
      html, item['video'] = extract_content_videos(content)
      if item['video']:
        item['content_type'] = 1
      else:
        item['content_type'] = 0
      # format html
      html = strip_html_attrs(html)
      html = re.sub(r'</?[^p!][^>]*>','',html)
      item['content'] = html
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    return None
