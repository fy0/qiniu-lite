# -*- coding: utf-8 -*-

import os
import hmac
import time
try:
    import ujson as json
except ImportError:
    import json
import mimetypes
import functools

try:
    from urlparse import urlparse  # py2
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlparse # py3
    from urllib.parse import urlencode

from hashlib import sha1

import requests

import sys
if sys.version > '3':
    basestring = str
    from base64 import urlsafe_b64encode as _urlsafe_b64encode
    
    def urlsafe_b64encode(data):
        if type(data) == str:
            data = bytes(data, 'utf-8')
        return str(_urlsafe_b64encode(data), 'utf-8')

else:
    from base64 import urlsafe_b64encode

version_info = (1, 0, 0)
VERSION = __version__ = '.'.join( map(str, version_info) )


"""
Usage:
cow = Cow(ACCESS_KEY, SECRET_KEY)
b = cow.get_bucket(BUCKET)
b.put('a')
b.put('a', 'b')
b.put('a', names={'a': 'x'})
b.put('a', 'b', names={'a': 'x', 'b': 'y'})
b.stat('a')
b.stat('a', 'b')
b.delete('a')
b.delete('a', 'b')
b.copy('a', 'c')
b.copy(('a', 'c'), ('b', 'd'))
b.move('a', 'c')
b.move(('a', 'c'), ('b', 'd'))
"""



RS_HOST = 'http://rs.qbox.me'
UP_HOST = 'http://up.qbox.me'
RSF_HOST = 'http://rsf.qbox.me'


class CowException(Exception):
    def __init__(self, url, status_code, content):
        self.url = url
        self.status_code = status_code
        self.content = content
        Exception.__init__(self, '%s' % content)



def signing(secret_key, data):
    try:
        return urlsafe_b64encode(
            hmac.new(secret_key, data, sha1).digest()
        )
    except:
        if type(secret_key) == str:
            secret_key = bytes(secret_key, 'ascii')
 
        if type(data) == str:
            data = bytes(data, 'utf-8')

        return urlsafe_b64encode(
            hmac.new(secret_key, data, sha1).digest()
        )


def sign_with_data(access_key, secret_key, b):
    data = urlsafe_b64encode(b)
    return '%s:%s:%s' % (access_key, signing(secret_key, data), data)


def requests_error_handler(func):
    @functools.wraps(func)
    def deco(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssertionError as e:
            req = e.args[0]
            raise CowException(
                    req.url, req.status_code, req.text
                )
    return deco

def expected_argument_type(pos, types):
    def deco(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            if not isinstance(args[pos], types):
                raise TypeError(
                    "{0} Type error, Expected {1}".format(args[pos], types)
                )
            return func(*args, **kwargs)
        return wrap
    return deco


class UploadToken(object):
    def __init__(self, access_key, secret_key, scope, ttl=3600):
        self.access_key = access_key
        self.secret_key = secret_key
        self.scope = scope
        self.ttl = ttl
        self._token = None
        self.generated = int(time.time())

    @property
    def token(self):
        if int(time.time()) - self.generated > self.ttl - 60:
            # 还有一分钟也认为过期了， make new token
            self._token = self._make_token()
        if not self._token:
            self._token = self._make_token()
        return self._token

    def _make_token(self):
        self.generated = int(time.time())
        info = {
            'scope': self.scope,
            'deadline': self.generated + self.ttl
        }

        info = urlsafe_b64encode(json.dumps(info))
        token = signing(self.secret_key, info)
        return '%s:%s:%s' % (self.access_key, token, info)
        



class Cow(object):
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.upload_tokens = {}
        
        self.stat = functools.partial(self._stat_rm_handler, 'stat')
        self.delete = functools.partial(self._stat_rm_handler, 'delete')
        self.copy = functools.partial(self._cp_mv_handler, 'copy')
        self.move = functools.partial(self._cp_mv_handler, 'move')

    def get_bucket(self, bucket):
        """对一个bucket的文件进行操作，
        推荐使用此方法得到一个bucket对象,
        然后对此bucket的操作就只用传递文件名即可
        """
        return Bucket(self, bucket)

    def get_put_policy(self, scope, expires=3600):
        """返回一个PutPolicy，这个是用于form上传文件的。"""
        return PutPolicy(self, scope, expires)

    def generate_access_token(self, url, params=None):
        uri = urlparse(url)
        token = uri.path
        if uri.query:
            token = '%s?%s' % (token, uri.query)
        token = '%s\n' % token
        if params:
            if isinstance(params, basestring):
                token += params
            else:
                token += urlencode(params)
        return '%s:%s' % (self.access_key, signing(self.secret_key, token))

    def build_requests_headers(self, token):
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'QBox %s' % token
        }

    @requests_error_handler
    def api_call(self, url, params=None):
        token = self.generate_access_token(url, params=params)
        if params:
            res = requests.post(url, data=params, headers=self.build_requests_headers(token))
        else:
            res = requests.post(url, headers=self.build_requests_headers(token))
        assert res.status_code == 200, res
        return json.loads(res.text) if res.text else ''


    def list_buckets(self):
        """列出所有的buckets"""
        url = '%s/buckets' % RS_HOST
        return self.api_call(url)

    def create_bucket(self, name):
        """不建议使用API建立bucket
        测试发现API建立的bucket默认无法设置<bucket_name>.qiniudn.com的二级域名
        请直接到web界面建立
        """
        url = '%s/mkbucket/%s' % (RS_HOST, name)
        return self.api_call(url)


    def drop_bucket(self, bucket):
        """删除整个bucket"""
        url = '%s/drop/%s' % (RS_HOST, bucket)
        return self.api_call(url)


    def list_files(self, bucket, marker=None, limit=None, prefix=None):
        """列出bucket中的文件"""
        query = ['bucket=%s' % bucket]
        if marker:
            query.append('marker=%s' % marker)
        if limit:
            query.append('limit=%s' % limit)
        if prefix:
            query.append('prefix=%s' % prefix)
        url = '%s/list?%s' % (RSF_HOST, '&'.join(query))
        return self.api_call(url)


    def generate_upload_token(self, scope, ttl=3600):
        """上传文件的uploadToken"""
        if scope not in self.upload_tokens:
            self.upload_tokens[scope] = UploadToken(self.access_key, self.secret_key, scope, ttl=ttl)
        return self.upload_tokens[scope].token


    @requests_error_handler
    @expected_argument_type(2, (basestring, list, tuple))
    def put(self, scope, filename, names=None, use_key_as_name=True):
        """上传文件
        filename 如果是字符串，表示上传单个文件，
        如果是list或者tuple，表示上传多个文件

        names 是dict，key为filename, value为上传后的名字
        如果不设置，默认为Hash值
        """
        url = '%s/upload' % UP_HOST
        token = self.generate_upload_token(scope)
        names = names or {}

        def _uploaded_name(filename):
            return names.get(filename, None) or os.path.basename(filename)
        
        def _put(filename):
            files = {
                'file': (filename, open(filename, 'rb')),
            }
            if use_key_as_name:
                action = '/rs-put/%s' % urlsafe_b64encode(
                    '%s' % (scope)
                )
            else:
                action = '/rs-put/%s' % urlsafe_b64encode(
                    '%s:%s' % (scope, _uploaded_name(filename))
                )
            _type, _encoding = mimetypes.guess_type(filename)
            if _type:
                action += '/mimeType/%s' % urlsafe_b64encode(_type)
            data = {
                'auth': token,
                'action': action,
            }
            res = requests.post(url, files=files, data=data)
            assert res.status_code == 200, res
            return json.loads(res.text)
        
        if isinstance(filename, basestring):
            # 单个文件
            return _put(filename)
        # 多文件
        return [_put(f) for f in filename]



    @expected_argument_type(2, (list, tuple))
    def _cp_mv_handler(self, action, args):
        """copy move方法
        action: 'copy' or 'move'
        args: [src_bucket, src_filename, des_bucket, des_filename]
        or [(src_bucket, src_filename, des_bucket, des_filename), (), ...]
        args 第一种形式就是对一个文件进行操作，第二种形式是多个文件批量操作

        用户不用直接调用这个方法
        """
        if isinstance(args[0], basestring):
            return self._cp_mv_single(action, args)
        if isinstance(args[0], (list, tuple)):
            return self._cp_mv_batch(action, args)


    @expected_argument_type(3, (basestring, list, tuple))
    def _stat_rm_handler(self, action, bucket, filename):
        """stat delete方法
        action: 'stat' or 'delete'
        bucket: 哪个bucket
        filenmae: 'aabb' or ['aabb', 'ccdd', ...]
        filename 第一种形式就是对一个文件进行操作，第二种形式是多个文件批量操作

        用户不用直接调用这个方法
        """
        if isinstance(filename, basestring):
            return self._stat_rm_single(action, bucket, filename)
        if isinstance(filename, (list, tuple)):
            return self._stat_rm_batch(action, bucket, filename)
    
    
    def _cp_mv_single(self, action, args):
        src_bucket, src_filename, des_bucket, des_filename = args
        url = '%s/%s/%s/%s' % (
            RS_HOST,
            action,
            urlsafe_b64encode('%s:%s' % (src_bucket, src_filename)),
            urlsafe_b64encode('%s:%s' % (des_bucket, des_filename)),
        )
        return self.api_call(url)
    
    def _cp_mv_batch(self, action, args):
        url = '%s/batch' % RS_HOST
        def _one_param(arg):
            return 'op=/%s/%s/%s' % (
                action,
                urlsafe_b64encode('%s:%s' % (arg[0], arg[1])),
                urlsafe_b64encode('%s:%s' % (arg[2], arg[3])),
            )
        param = '&'.join( map(_one_param, args) )
        return self.api_call(url, param)


    def _stat_rm_single(self, action, bucket, filename):
        url = '%s/%s/%s' % (
            RS_HOST, action, urlsafe_b64encode('%s:%s' % (bucket, filename))
        )
        return self.api_call(url)


    def _stat_rm_batch(self, action, bucket, filenames):
        url = '%s/batch' % RS_HOST
        param = [
            'op=/%s/%s' % (
                action, urlsafe_b64encode('%s:%s' % (bucket, f))
            ) for f in filenames
        ]
        param = '&'.join(param)
        return self.api_call(url, param)






def transform_argument(func):
    @functools.wraps(func)
    def deco(self, *args, **kwargs):
        filename = args[0] if len(args) == 1 else args
        return func(self, filename, **kwargs)
    return deco
        

class Bucket(object):
    def __init__(self, cow, bucket):
        self.cow = cow
        self.bucket = bucket

    @transform_argument
    def put(self, *args, **kwargs):
        names = kwargs.get('names', None)
        if names and not isinstance(names, dict):
            raise TypeError(
                "names Type error, Expected dict, But got Type of {0}".format(type(names))
            )
        return self.cow.put(self.bucket, args[0], names=names)

    @transform_argument
    def stat(self, *args):
        return self.cow.stat(self.bucket, args[0])

    @transform_argument
    def delete(self, *args):
        return self.cow.delete(self.bucket, args[0])

    @transform_argument
    def copy(self, *args):
        return self.cow.copy(self._build_cp_mv_args(args[0]))
        
    @transform_argument
    def move(self, *args):
        return self.cow.move(self._build_cp_mv_args(args[0]))

    def list_files(self, marker=None, limit=None, prefix=None):
        return self.cow.list_files(self.bucket, marker=marker, limit=limit, prefix=prefix)


    def _build_cp_mv_args(self, filename):
        if isinstance(filename[0], basestring):
            args = [self.bucket, filename[0], self.bucket, filename[1]]
        else:
            args = []
            for src, des in filename:
                args.append( (self.bucket, src, self.bucket, des) )
        return args


class PutPolicy(object):
    scope = None             # 可以是 bucketName 或者 bucketName:key
    expires = 3600           # 默认是 3600 秒

    def __init__(self, cow, scope, expires=3600):
        self.cow = cow
        self.scope = scope
        self.expires = expires

    def token(self):
        token = dict(
            scope = self.scope,
            deadline = int(time.time()) + self.expires,
        )

        params = ['callbackUrl', 'callbackBody', 'returnUrl', 'returnBody',
            'endUser', 'asyncOps', 'saveKey', 'exclusive', 'detectMime',
            'fsizeLimit', 'persistentOps', 'persistentNotifyUrl']

        for i in params:
            if hasattr(self, i):
                token[i] = getattr(self, i)

        #import json
        #b = json.dumps(token, separators=(',',':'))
        b = json.dumps(token)
        return sign_with_data(self.cow.access_key, self.cow.secret_key, b)

