import re
import traceback
from datetime import datetime
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, format_url
from .default import DefaultSiteParser

class AlarabiyaSiteParser(DefaultSiteParser):

  # return value: (found_list_page(bool), next_links) 
  def search_list_page(self, response):
    link = response.url.replace('http://www.alarabiya.net', '')
    next_links = None
    # level = link.count('/')
    more_btn_links = response.css('div.content div.arena a.more').xpath('@href').extract()
    if '/archive' in link and not more_btn_links:
      return True, link
    elif more_btn_links:
      next_links = more_btn_links
    return False, next_links

  def parse_article_urls(self, response):
    return response.css('div.box.articles_archive div.arena div.item a.highline').xpath('@href').extract()

  def parse_next_page_url(self, response):
    page_urls = response.css('ul.paging li a')
    if page_urls and page_urls[-1].css('::text').re('[^,\d1]+'):
      return page_urls[-1].xpath('@href').extract_first()
    
  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('article.multi_articles div.highline span::text').extract_first()
      pass
      item['author'] = response.css('article.multi_articles div.source::text').extract_first() or ''
      date_str = response.css('article.multi_articles div.date').xpath('time/@datetime').extract_first() or ''
      time_strs = response.css('article.multi_articles div.caption').re('GMT\s+(\d\d:\d\d)')
      if time_strs:
        date_str = date_str + ' ' + time_strs[0]
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int((datetime.strptime(date_str,'%Y-%m-%d %H:%M')).timestamp()*1000)
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      item['abstract'] = extra_info.get('abstract') or ''
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('div.article-body')
      thumbnail_selector = response.css('div.article_img img')
      if thumbnail_selector:
        print('found thumbnail: %s' % thumbnail_selector.extract_first())
      item['content'], item['img'] = strip_html_imgs(
          content_selector, thumbnail_selector)
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None  # illegal flag
      return

  def parse_category_url(self, response):
    parent_page_links = response.css('ul.breadcrumbs li a')
    if parent_page_links:
      category_url = parent_page_links[-1].xpath('@href').extract_first().replace('.html','/archive.news.html')
      if category_url:
        match_res = re.search(r'^(/[^/]+)', category_url)
        return match_res and 'http://www.alarabiya.net%s' % match_res.group(0)