import re
import traceback
from datetime import datetime
from functools import reduce
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import parse_arabic_date, strip_html_imgs, hash_digest, format_url, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

DATE_PATTERN = re.compile('\d{2}\D+20\d{2}')

class AawsatSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    return response.css('#ac_small div.views-row div.views-field-view-node span.field-content').xpath('a/@href').extract()

  def parse_next_page_url(self, response):
    return response.xpath(
        '//ul[@class="pagination"]/li[@class="next last"]/a/@href').extract_first()

  def __get_thumbnail_selector(self, response):
    thumbnail_selector = response.css(
        '#article_content .node_new_photo') or response.css('ul.amazingslider-slides li img')
    return thumbnail_selector

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = format_url(response.url)
    item['id'] = hash_digest(item.get('original_url'))
    try:
      item['scr'] = extra_info.get('scr')  # seed source id
      item['cid'] = extra_info.get('cid')  # cid
      item['media'] = extra_info.get('media_id')  # media: news_medias
      item['title'] = response.css(
          'div#article_content h2::text').extract_first()
      item['author'] = response.css(
          '.node_new_resource::text').extract_first() or ''  # author
      date_str = response.css('div#update_date::text').extract_first()
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        post_time = parse_arabic_date(date_str, DATE_PATTERN)
        if post_time:
          post_id = 0
          try:
            post_id = int(re.search('\d{6}', response.url).group())
          except Exception as e:
            print('parse post id failed', e)
            traceback.print_exc()
            post_id = 0
          item['release_time'] = int(
              post_time.timestamp()*1000 + (post_id % 10000))
        else:
          item['release_time'] = 0
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      item['abstract'] = ''
      item['url'] = ''
      content_selector = response.css('#article_content .node_new_body')
      thumbnail_selector = self.__get_thumbnail_selector(response)
      if thumbnail_selector:
        print('found thumbnail: %s' % thumbnail_selector.extract_first())
      content, item['img'] = strip_html_imgs(content_selector, thumbnail_selector)  # imgs desc: JSON
      # extract videos
      html, item['video'] = extract_content_videos(content)
      if item['video']:
        item['content_type'] = 1
      else:
        item['content_type'] = 0
      # format html
      html = strip_html_attrs(html)
      html = re.sub(r'</?[^p!b][^>]*>','',html)
      # first_div = re.search(r'<div>.*</div>', html).group(0)
      paras = list(filter(None, html.split('<br>')))
      # html = reduce(lambda x,y : '%s<p>%s</p>' % (x, y), paras, first_div)
      html = reduce(lambda x,y : '%s<p>%s</p>' % (x, y), paras, '')
      item['content'] = html
      return item
    except Exception as e:
      print('failed to parse_article, url: %s' % response.url, e)
      traceback.print_exc()
      item['recom_time'] = None

  def parse_category_url(self, response):
    parent_page_links = response.css('ul.breadcrumbs li a')