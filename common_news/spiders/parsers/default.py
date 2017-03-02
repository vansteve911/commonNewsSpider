class DefaultSiteParser(object):

  def search_list_page(self, response):
    raise Exception('search_list_page not implemented!')

  def parse_article_urls(self, response):
    raise Exception('parse_article_urls not implemented!')

  def parse_next_page_url(self, response):
    raise Exception('parse_next_page_url not implemented!')

  def parse_article_item(self, response, extra_info):
    raise Exception('parse_article_item not implemented!')

  def parse_category_url(self, response):
    raise Exception('parse_category_url not implemented!')