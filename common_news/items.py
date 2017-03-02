# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import traceback
from scrapy import Item, Field

DISPLAY_LEN = 20

class CommonNewsItem(scrapy.Item):
  id = Field()
  scr = Field()  # seed source id
  cid = Field()  # channel id
  media = Field()  # media: news_medias
  title = Field()  # title
  author = Field()  # author
  release_time = Field()  # article post time, timestamp
  recom_time = Field()  # fetch time, timestamp
  abstract = Field()  # abstract
  content_type = Field() # content_type: 0: 普通正文, 1:图集正文, 2: webview,4. 导流. 注：这版数据类型和内容类型先合并为一个字段
  original_url = Field()  # original url
  url = Field()  # generated url TODO
  content = Field()  # content
  img = Field()  # imgs desc: JSON array string
  video = Field()  # video desc: JSON array string

  def __repr__(self):
    return repr({
      'id': self['id'],
      'title': self['title'],
      'author': self['author'],
      'release_time': self['release_time'],
      'recom_time': self['recom_time'],
      'abstract': self['abstract'][:DISPLAY_LEN],
      'content_type': self['content_type'],
      'original_url': self['original_url'],
      'url': self['url'],
      'content': self['content'][:DISPLAY_LEN],
      'img': self['img'],
      'video': self.get('video'),
      'cid_id': self['cid'],
      'media_id': self['media'],
      'scr_id': self['scr'],
    })

  def parse_db_obj(self):
    import json
    try:
      img = json.dumps(self['img'], ensure_ascii=False)
      video = json.dumps(self.get('video'), ensure_ascii=False)
      return {
          'id': self['id'],
          'title': self['title'],
          'author': self['author'],
          'release_time': self['release_time'],
          'recom_time': self['recom_time'],
          'abstract': self['abstract'],
          'content_type': self['content_type'],
          'original_url': self['original_url'],
          'url': self['url'],
          'content': self['content'],
          'img': img,
          'video': video,
          'cid_id': self['cid'],
          'media_id': self['media'],
          'scr_id': self['scr'],
      }
    except Exception as e:
      print('parse db obj failed, %s' % self, e)
      traceback.print_exc(),
