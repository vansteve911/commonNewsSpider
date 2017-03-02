# -*- coding: utf-8 -*-
import os
import traceback
import requests
from datetime import datetime
from .common.utils import hash_digest, get_postfix
from .common.oss_client import OssClient
from .common.db_client import DbClient
from .decorators.checkers import check_spider_pipeline
from PIL import Image
from io import BytesIO

class ImgUploadPipeline(object):

  def __init__(self, oss_config):
    self.oss_client = OssClient(oss_config)

  @classmethod
  def from_crawler(cls, crawler):
    return cls(
        oss_config=crawler.settings.get('OSS')
    )

  @check_spider_pipeline
  def process_item(self, item, spider):
    if not item:
      return
    if item['img']:
      for img in item['img']:
        upload_url = self.__upload_img(img)
        if upload_url:
          spider.log('upload success, ori url: %s, new url: %s' %
                (img['original_url'], upload_url))
          img['url'] = upload_url
          del img['original_url']
    else:
      spider.log('no imgs! item url :%s' % item['url'])
    # upload video iurl
    if item['video']:
      for video in item['video']:
        iurl = self.__upload_video_iurl(video)
        if iurl:
          video['iurl'] = iurl
    else:
      spider.log('no video iurls! item url :%s' % item['url'])
    return item

  def __upload_img(self, img, filename=None):
    url = img['original_url']
    if not filename:
      filename = hash_digest(url)
      postfix = get_postfix(url)
      if postfix:
        filename = filename + postfix
      print('upload filename: %s' % filename)
    try:
      print('getting img from %s ...' % url)
      indata = requests.get(url)
      upload_url = self.oss_client.upload(indata, filename)
      if upload_url:
        self.__append_img_info(img, indata)
        return upload_url
    except Exception:
      print('error requesting url: %s' % url)
      traceback.print_exc()

  def __upload_video_iurl(self, video, filename=None):
    url = video.get('iurl')
    if not filename:
      filename = hash_digest(url)
      postfix = get_postfix(url)
      if postfix:
        filename = filename + postfix
      print('upload filename: %s' % filename)
    try:
      print('getting video iurl from %s ...' % url)
      indata = requests.get(url)
      return self.oss_client.upload(indata, filename)
    except Exception:
      print('error requesting url: %s' % url)
      traceback.print_exc()

  def __append_img_info(self, img, indata):
    if img['width'] and img['height']:
      return
    try:
      img_obj = Image.open(BytesIO(indata.content))
      if img_obj:
        print('get img info, size: %s, format: %s, url: %s' %
              (img_obj.size, img_obj.format, img['url']))
        img['width'] = img_obj.width
        img['height'] = img_obj.height
      # pass
    except Exception:
      print('error when appending img info, img: %s' % img)
      traceback.print_exc()

class DuplicateJudgePipeline(object):
  def __init__(self, db_config):
    self.db_client = DbClient(db_config)

  @classmethod
  def from_crawler(cls, crawler):
    return cls(
        db_config=crawler.settings.get('DB')
    )

  @check_spider_pipeline
  def process_item(self, item, spider):
    spider.log('into DuplicateJudgePipeline')
    if item:
      if not item.get('cid') or not item.get('media'):
        spider.log('empty cid of media!! %s ' % item)
        return
      # find same id record in DB
      sql = '''SELECT id, fetch_status FROM fetch_articles WHERE id = %s'''
      same_id_record = self.db_client.query_one(sql, (item['id']))
      spider.log('same_id_record: %s' % same_id_record)
      if same_id_record:
        if same_id_record.get('fetch_status') == 2:
          # overwrite new item recom_time
          item.update({
            'recom_time': same_id_record.get('recom_time'),
            # 'fetch_status': 0
          })
          spider.log('overwrite recom_time & fetch_status of refetched item: %s' % item)
          return item
        else:
          spider.log('duplicated item found: %s' % item['id'])
      else:
        return item

class ExportHTMLPipeline(object):
  def __init__(self):
    from .common.html_template import template
    self.template = template

  @staticmethod
  def __parse_html_img(content, imgs):
    ref = 0
    for img in imgs:
      content = content.replace('<!--{img:%d}-->' % ref, 
        '<img src="%s">' % (img['url'] or img['original_url']))
      ref += 1
    return content

  @check_spider_pipeline
  def process_item(self, item, spider):
    if not item:
      return
    html = self.template
    obj = item.parse_db_obj()
    obj['release_time'] = datetime.fromtimestamp(obj['release_time']/1000).strftime('%Y-%m-%d-%H-%M')
    obj['content'] = self.__parse_html_img(item['content'], item['img'])
    for (k, v) in obj.items():
      html = html.replace('{%s}' % k, str(v))
    if html:
      filename = '/tmp/crawled/prv_%s_%s_%s.html' % (obj['release_time'], obj['cid_id'], obj['id'])
      with open(filename, 'w+') as f:
        f.write(html)
    return item

class DbStorePipeline(object):

  def __init__(self, db_config):
    self.db_client = DbClient(db_config)

  @classmethod
  def from_crawler(cls, crawler):
    return cls(
        db_config=crawler.settings.get('DB')
    )

  def __insert_failed_record(self, obj):
    insert_sql = '''REPLACE INTO fetch_articles (id, fetch_status, recom_time, original_url) VALUES
(%s, %s, %s, %s)'''
    params = (obj['id'],
              2,
              int(datetime.now().timestamp()*1000),
              obj['original_url'])
    res = self.db_client.execute(insert_sql, params)
    print('fetch failed, insert failed record into DB, id: %s, success: %s' % (obj.get('id'), res))

  @check_spider_pipeline
  def process_item(self, item, spider):
    # spider.log('into DbStorePipeline, item: ', item)
    if item:
      if not item.get('release_time'):
        spider.log('found invalid item: ', item)
        self.__insert_failed_record(item)
        return
      obj = item.parse_db_obj()
      if obj:
        insert_sql = '''REPLACE INTO fetch_articles
(id, title, author, release_time, recom_time, abstract, content_type, original_url, url, content, img, cid_id, media_id, scr_id, video) VALUES
(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        params = (obj['id'],
                  obj['title'],
                  obj['author'],
                  obj['release_time'],
                  obj['recom_time'],
                  obj['abstract'],
                  obj['content_type'],
                  obj['original_url'],
                  obj['url'],
                  obj['content'],
                  obj['img'],
                  obj['cid_id'],
                  obj['media_id'],
                  obj['scr_id'],
                  obj['video'])
        res = self.db_client.execute(insert_sql, params)
        spider.log('insert item [%s] into DB, success: %s' % (obj['id'], res))
      if not res and (obj.get('id') and obj.get('original_url')):
        self.__insert_failed_record(obj)
    return item
