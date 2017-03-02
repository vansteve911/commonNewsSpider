import oss2


class OssClient(object):

  def __init__(self, oss_config):
    self.access_key = oss_config['ACCESS_KEY']
    self.access_secret = oss_config['ACCESS_SECRET']
    self.endpoint = oss_config['ENDPOINT']
    self.bucket_name = oss_config['BUCKET_NAME']
    self.prefix = oss_config['PREFIX']
    self.auth = oss2.Auth(self.access_key, self.access_secret)
    self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
    self.host = '%s.%s' % (self.bucket_name, self.endpoint)

  def upload(self, input_data, filename):
    upload_uri = self.prefix + filename
    res = self.bucket.put_object(upload_uri, input_data)
    url = ('http://%s/%s' % (self.host, upload_uri))
    print('upload url data to remote[%s], result: %s' % (url, res))
    if res:
      return url
