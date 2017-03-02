import re
import traceback
from datetime import datetime
import dateparser
from ...items import CommonNewsItem
from ...common.config import SpiderSeeds
from ...common.utils import strip_html_imgs, hash_digest, extract_content_videos, strip_html_attrs
from .default import DefaultSiteParser

class NasSiteParser(DefaultSiteParser):

  def search_list_page(self, response):
    return True, None

  def parse_article_urls(self, response):
    list_page_parse_res = response.css('div.n_content div.n_comment p a.n_color.n_read_more').xpath('@href').extract()
    main_page_parse_res = response.css('div.n_category_list_items a.n_color.n_read_more').xpath('@href').extract()
    return ['/%s' % x for x in list_page_parse_res + main_page_parse_res]

  def parse_next_page_url(self, response):
    next_page_sel = response.css('div.n_content div.pagination.n_pagination li')
    if next_page_sel:
      next_page_sel = next_page_sel[-1]
      if next_page_sel.xpath('a/font/text()').re('\D'):
        return '/%s' % next_page_sel.xpath('a/@href').extract_first()
    else:
      more_btn_sel = response.css('button#SendYourOpinion.btn.jmhorcolor')
      if more_btn_sel: 
        match = re.search(r'NewsTypeID=(\d+)',response.url)
        if match:
          return '/NewsMoreResultAR.asp?NewsTypeID=%s' % match.group(1)

  def parse_article_item(self, response, extra_info):
    item = CommonNewsItem()
    item['original_url'] = response.url
    item['id'] = hash_digest(response.url)
    try:
      item['scr'] = extra_info.get('scr')
      item['cid'] = extra_info.get('cid')
      item['media'] = extra_info.get('media_id')
      item['title'] = response.css('div.n_content div.span12.n_blog_list.n_post div div h1::text').extract_first()
      item['author'] = ''
      date_str = response.css('div.n_content div.span12.n_blog_list.n_post span.n_little_date::text').re('\d{4}/\d{1,2}/\d{1,2}\s+\d{2}:\d{2}:\d{2}')
      if date_str:
        date_str = date_str[0]
      else:
        date_str = ''
      if extra_info.get('release_time'):
        item['release_time'] = extra_info.get('release_time')
      else:
        item['release_time'] = int((dateparser.parse(date_str).timestamp()*1000))
      item['recom_time'] = int(datetime.now().timestamp()*1000)
      abstract = extra_info.get('abstract') or response.css('div.n_content span.n_little_date_s::text').extract_first()
      # item['abstract'] = abstract.replace('\r', '').replace('\n', '').replace('\t', '')
      item['abstract'] = ''
      item['content_type'] = 0
      item['url'] = ''
      content_selector = response.css('div.n_content div.span12.n_blog_list.n_post').xpath('descendant::div[@style="padding-top:45px;"]')
      thumbnail_selector = response.css('div.n_content div.span12.n_blog_list.n_post').xpath('descendant::div[@style="padding-top:45px;padding-bottom:0px"]').xpath('following-sibling::img')
      content, item['img'] = strip_html_imgs(
          content_selector, thumbnail_selector, host = 'http://nas.sa/')
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
    return 'http://nas.sa/' + response.css('div.row-fluid ul.pull-right li a img.tickerunder').xpath('parent::a/@href').extract_first()
