# -*- coding: utf-8 -*-

from dateparser import parse
import re
import traceback
from functools import reduce

IMG_PATTERN = re.compile('<img[^>]+>')
IMG_SIZE_PATTERN = re.compile('\d+')
POSTFIX_PATTERN = re.compile('\.\w+$')
VALID_HTML_TAGS = ['p', 'br']
INVALID_PATTERNS = [
    re.compile('<script[^>]*>[^<]*[^/]*</script>'),
    re.compile('<style[^>]*>.*</style>'),
    re.compile('<iframe[^>]*>.*</iframe>'),
]
ESCAPE_CHARS = {'&nbsp;': ' ',
                # 'lt':'<','60':'<',
                # 'gt':'>','62':'>',
                '&amp;': '&',
                '&quot;': '"', }
ESCAPE_PATTERN = re.compile(r'&#?(?P<name>\w+);')
HTML_TAG_PATTERN = re.compile('</?(\w+)[^>]*>')
URL_HOST_PATTERN = re.compile('http[s]?://[^/]+/')

TITLE_ATTR_NAMES = ['title', 'alt']
DESC_ATTR_NAMES = ['data-description', 'description', 'alt']


def get_url_host(url):
  if isinstance(url, str):
    match = URL_HOST_PATTERN.search(url)
    if match:
      return match.group(0)


def load_lines_in_file(file):
  try:
    lines = []
    with open(file) as f:
      while True:
        line = f.readline()
        if line:
          lines.append(line.replace('\n', ''))
        else:
          break
    return lines
  except Exception as e:
    print('error loading lines in file %s' % lines, e)
    traceback.print_exc()


def parse_arabic_date(input, pattern=None):
  if pattern != None:
    match = pattern.search(input)
    if match:
      input = match.group(0)
  if input:
    return parse(input)


def get_postfix(path):
  if isinstance(path, str):
    match = POSTFIX_PATTERN.search(path.split('?')[0])
    if match:
      return match.group(0)


def __parse_img_size_attr(img_sel, attr_name):
  attr = img_sel.xpath('@'+attr_name).extract_first()
  if isinstance(attr, str):
    match = re.search(IMG_SIZE_PATTERN, attr)
    if match:
      return int(match.group())
  return 0


def filter_html_tags(html, valid_tags=None):
  if not html:
    return ''
  # print('raw html: ', html)
  if not isinstance(valid_tags, list):
    valid_tags = VALID_HTML_TAGS
  for pattern in INVALID_PATTERNS:
    # print('pattern::::::', pattern, '::::raw html::::', html)
    html = re.sub(pattern, '', html)
    # print('replaced html', html)
  tag_iter = re.finditer(HTML_TAG_PATTERN, html)
  strs_to_filter = filter(None,
                          [((m.group(1) not in valid_tags) and m.group(0)) for m in tag_iter] + ['\n', '\t'])
  ret = reduce(lambda h, t: h.replace((t or ''), ''), strs_to_filter, html)
  # replcae
  # esc_iter = re.finditer(ESCAPE_PATTERN, ret)
  for (k, v) in ESCAPE_CHARS.items():
    ret = ret.replace(k, v)
  # print('ret: ', ret)
  return ret


def strip_html_imgs(content_selector, thumbnail_selector=None, host=None, custom_filter_xpath=None):
  imgs = []
  # replace unwanted elements
  if not custom_filter_xpath:
    custom_filter_xpath = 'descendant::p[not(contains(@style,"display"))]|descendant::div//img|br|text()'
  content_selector = content_selector.xpath(custom_filter_xpath)
  # print('content_sel:', content_selector)
  if len(content_selector) > 0:
    selectors = content_selector
  else:
    selectors = [content_selector]
  if thumbnail_selector:
    selectors = thumbnail_selector + selectors
  l = [s.css('img') for s in selectors]
  img_sels = [item for sublist in l for item in sublist]
  for img_sel in img_sels:
    url = img_sel.xpath('@src').extract_first() or ''
    if host:
      url = host + url
    title = ''
    description = ''
    width = __parse_img_size_attr(img_sel, 'width')
    height = __parse_img_size_attr(img_sel, 'height')
    # if parse_description:
    #   for attr_name in TITLE_ATTR_NAMES:
    #     title = title or img_sel.xpath('@'+attr_name).extract_first() or ''
    #   for attr_name in DESC_ATTR_NAMES:
    #     description = description or img_sel.xpath(
    #         '@'+attr_name).extract_first() or ''
    # else:
    #   title = ''
    #   description = ''
    imgs.append({
        'original_url': url,
        'url': '',
        'title': title,
        'description': '', # don't need
        'width': width,
        'height': height,
    })
  html_sels = content_selector.extract()
  if thumbnail_selector:
    html_sels = thumbnail_selector.extract() + html_sels
  content = reduce(lambda x, y: x+y, html_sels, '')
  content = reduce(lambda h, t: h.replace((t or ''), ''), ['\n', '\t', '\r\n'], content)
  ref = 0
  while True:
    tmp_content = IMG_PATTERN.sub(('<!--{img:%d}-->' % ref), content, 1)
    if tmp_content == content:
      break
    content = tmp_content
    ref = ref + 1
  # content = filter_html_tags(content)
  return content, imgs

# returns content, videos
def extract_content_videos(content, video_tag_pattern = None):
  if not video_tag_pattern:
    video_tag_pattern = re.compile('<iframe[^>]+>[^<]*</iframe>')
  video_tags = [m.group(0) for m in re.finditer(video_tag_pattern, content)]
  ids = [re.search('www.youtube.com/embed/([^?"/]+)', tag).group(1) for tag in video_tags]
  videos = [get_youtube_video_info(id) for id in ids] or []
  return reduce(lambda h, i: h.replace(video_tags[i], '<!--{video:%d}-->' % i), range(0, len(video_tags)), content), videos


def format_url(url, sort_query_keys=False, strip_encoded_query=False):
  import urllib.parse

  def has_urlencoded(s):
    return re.search(r'(%[a-fA-F0-9]{2})+', s)
  if url:
    mapping = urllib.parse.urlparse(url)
    encoded_query = ''
    if mapping.query:
      q_tuple = tuple(kv.split('=') for kv in mapping.query.split('&'))
      query_map = {k: urllib.parse.quote(v) for k, v in q_tuple}
      query_keys = query_map.keys()
      if strip_encoded_query:
        query_keys = filter(
            lambda k: not has_urlencoded(query_map.get(k)), query_keys)
      if sort_query_keys:
        query_keys = sorted(query_keys)
      encoded_query = '?' + \
          '&'.join([('%s=%s' % (k, query_map.get(k))) for k in query_keys])
    encoded_path = mapping.path
    if not has_urlencoded(encoded_path):
      encoded_path = urllib.parse.quote(mapping.path)
    encoded_path = re.sub(r'/$', '', encoded_path)
    encoded_path = re.sub(r'/{2,}', '/', encoded_path)
    return '%s://%s%s%s' % (mapping.scheme, mapping.netloc, encoded_path, encoded_query)

def hash_digest(input):
  import hashlib
  if input:
    hash_object = hashlib.md5(input.encode())
    return hash_object.hexdigest()

def get_youtube_video_info(id):
  import requests, urllib.parse
  VALID_VIDEO_INFO_KEYS = ['title', 'length_seconds', 'iurl']
  try:
    url = 'https://www.youtube.com/get_video_info?html5=1&video_id=%s' % id
    resp = requests.get(url)
    if resp and resp.status_code == 200:
      if 'errorcode' in resp.text:
        print('get video info failed, response: %s', resp.text)
        return None
      kvs = [kv.split('=') for kv in resp.text.split('&')]
      filtered_kvs = list(filter(lambda kv:kv[0] in VALID_VIDEO_INFO_KEYS, kvs))
      filtered_kvs.append(['youtube_id', id])
      return dict(map(lambda kv:(kv[0], urllib.parse.unquote(kv[1])), filtered_kvs))
    else:
      print('invalid response: %s', resp)
  except Exception as e:
    traceback()
  print('get youtube video info failed, id: %s' % id)
  return None

def strip_html_attrs(html):
  return re.sub(r'<(\w+)\s[^>]+>',r'<\1>',html)

if __name__ == '__main__':
  id = 'oFs05z8Zbis'
  print(get_youtube_video_info(id))
  