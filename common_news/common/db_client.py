import pymysql
import traceback


class DbClient(object):

  def __init__(self, config):
    self.host = config['MYSQL_HOST']
    self.port = config['MYSQL_PORT']
    self.db_name = config['MYSQL_DBNAME']
    self.user = config['MYSQL_USER']
    self.passwd = config['MYSQL_PASSWD']
    self.charset = config['MYSQL_CHARSET']

  def query_list(self, sql_tmpl, params):
    def query_func(cursor, sql):
      cursor.execute(sql)
      return cursor.fetchall()
    return self.execute(sql_tmpl, params, query_func)

  def query_one(self, sql_tmpl, params):
    def query_func(cursor, sql):
      cursor.execute(sql, params)
      return cursor.fetchone()
    return self.execute(sql_tmpl, params, query_func)

  def execute(self, sql, params, query_func=None):
    if not isinstance(sql, str):
      return
    connection = None
    try:
      connection = pymysql.connect(
          host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db_name, charset=self.charset)
      with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        if callable(query_func):
          # query
          return query_func(cursor, sql)
        else:
          # update query
          try:
            # 执行sql语句
            cursor.execute(sql, params)
            # 提交到数据库执行
            connection.commit()
            return True
          except Exception as e:
            # 如果发生错误则回滚
            print(
                'error occured when execute update, will rollback', e)
            traceback.print_exc()
            connection.rollback()
    except Exception as e:
      print('error occured!', e)
      traceback.print_exc()
    finally:
      if connection:
        connection.close()

if __name__ == '__main__':
  config = {
      'MYSQL_HOST': 'rm-gs56dp590mez7yl47o.mysql.singapore.rds.aliyuncs.com',
      'MYSQL_PORT': 3306,
      'MYSQL_DBNAME': 'ayu',
      'MYSQL_USER': 'root123',
      'MYSQL_PASSWD': 'Test12345',
  }
  db_client = DbClient(config)
  sql = '''INSERT INTO news_articles (id, title, author, release_time, recom_time, abstract, content_type, original_url, url, content, img, cid_id, media_id, scr_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
  params = ('test', 'title', 'author', 0, 0, 'abstract', 0,
            'original_url', 'url', 'content', 'img', 100000, 10001, 1000001)
  print(db_client.execute(sql, params))
