# -*- coding: utf-8 -*-
from .common.db_client import DbClient
from .decorators.singleton import singleton
from .settings import DB
from .common.utils import get_url_host, format_url

@singleton
class SeedManager():

  __seeds_by_name = {}
  __seeds_by_url = {}

  def __init__(self):
    db_config = DB
    self.db_client = DbClient(db_config)
    self.__load_seeds()

  def __load_seeds(self):
    print('loading spider seeds...')
    sql = '''SELECT * FROM news_seeds WHERE status = 1'''
    all_seeds = self.db_client.query_list(sql, [])
    print('loaded %d news seeds' % len(all_seeds))
    if all_seeds:
      self.__seeds_by_name = { seed.get('name'): seed for seed in all_seeds }
      self.__seeds_by_url = { format_url(seed.get('url'), sort_query_keys=True, strip_encoded_query=True): seed for seed in all_seeds }
      self.__nameprefixes_by_host = { get_url_host(seed.get('url')) : (seed.get('name').split('_'))[0] for seed in all_seeds }
  
  def get_seed_by_name(self, name):
    return self.__seeds_by_name.get(name)

  def get_seed_by_url(self, url):
    return self.__seeds_by_url.get(url)

  def search_seed_name_prefix(self, url):
    return self.__nameprefixes_by_host.get(get_url_host(url))
    
if __name__ == '__main__':
  seed_manager = SeedManager()
  print('almowaten_sport: \n', seed_manager.get_seed_by_name('almowaten_sport'))
  seed_manager2 = SeedManager()
  print('http://www.almowaten.net/category/mony/: \n', seed_manager2.get_seed_by_name('almowaten_economy'))
