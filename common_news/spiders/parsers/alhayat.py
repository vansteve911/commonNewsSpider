import re
import traceback
from datetime import datetime
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, format_url
from .default import DefaultSiteParser

class AlhayatSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('#TopicAllSub div.description a.descriptionBlueTilteLandingRT').xpath('@href').extract()

  def parse_next_page_url(self, response):
    return response.css('div.PagerNumberArea a.UnselectedNext').xpath('@href').extract_first()

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('div#ContentWrapper h1.ArticlesTitle::text').extract_first()
      item['author'] = response.css('div.ArticlesTitlesBox span.articletextRight a::text').extract_first() or ''
      date_str = response.css('div.ArticlesTitlesBox span.articletextLeft script').re('\d{4}\-\d\d\-\d\dT\d\d:\d\d:\d\d')
      date_str = date_str and date_str[0] or ''
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int((datetime.strptime(date_str,'%Y-%m-%dT%H:%M:%S')).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or ''
      item['abstract'] = abstract.replace('\n', '')
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('div#DetDescription')
      thumbnail_selector = response.css('div.ArticlesDetails div.mainImage img')
      item['content'], item['img'] = strip_html_imgs(
          content_selector, thumbnail_selector, host='http://www.alhayat.com/')
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    pass #!!!!!!!
    # return response.css('div#crumbs').xpath('div[@itemscope]').re('http://[^/]+/category/[^"]+/?')[0]

