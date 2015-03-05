# qiniu-lite 七牛

一个非常简单的七牛云存储 Python SDK

对网页表单上传和本地文件操作提供支持，同时兼容py2/3。


官方SDK在此：

[![官方SDK](http://qiniutek.com/images/logo-2.png)](https://github.com/qiniu/python-sdk)

## 安装

```bash
pip install qiniu-lite
```


## 使用

#### 初始化

在你的项目中
```python
from qiniu_lite import Cow
cow = Cow(<ACCESS_KEY>, <SECRET_KEY>)
# 获取 bucket 对象
bucket = cow.get_bucket(<BUCKET_NAME>)
# 获取安全策略
policy = cow.get_put_policy(<BUCKET_NAME>)
```

#### 网页表单上传

不管你使用什么web框架，请为模板传入一个值：
``{'token': policy.token()}``

随后在网页中添加一个表单，注意 {{ token }} 这个变量。
```html
<form method="post" action="http://upload.qiniu.com/" enctype="multipart/form-data">
  <input name="token" type="hidden" value="{{ token }}">
  <input name="file" type="file" />
  <input name="accept" type="hidden" />
  <input type="submit" />
</form>
```

完成（绝大部分人只需要这个功能）。


#### 本地使用

```python
# 列出所有的bucket
cow.list_buckets()
# 获取指定文件信息
cow.stat(<BUCKET_NAME>, <FILENAME>)

# 列出 bucket 的所有文件
bucket.list_files()
# 获取文件信息，单体/批量
bucket.stat('a')
bucket.stat('a', 'b', 'c')
# 删除文件
bucket.delete('a')
bucket.delete('a', 'b', 'c')
# 移动文件
bucket.move('a', 'c')
bucket.move(('a', 'c'), ('b', 'd'))
# 复制文件
bucket.copy('a', 'b')
bucket.copy(('a', 'b'), ('c', 'd'))

# 文件上传，返回值是文件信息
bucket.put('a')
bucket.put('a', 'b', 'c')

# 需要特别注意的一点是，默认情况下put上传后，
# 会使用文件本身哈希值(官方文件的key)作为上传后的名字，
# 你可以使用`names`参数来指定文件上传后应该是什么名字。
# 之所以这么做，是因为大多数时候我们不关心文件名是什么，
# 在表单上传中尤其明显，而且必须避免重名！
bucket.put('a', names={'a': 'x'})
bucket.put('a', 'b', names={'a': 'x', 'b': 'y'}) # ab改名xy
bucket.put('a', 'b', 'c', names={'c': 'z'})  # 只改变'c'的名字为'z'

```


#### 异常

以上操作任何错误都会引发异常， 只要请求api返回的不是200

所以安全的做法是这样：

```python
from qiniu_lite import CowException

try:
    b.copy(('a', 'b'), ('c', 'd'))
except CowException as e:
    print e.url         # 出错的url
    print e.status_code # 返回码
    print e.content     # api 错误的原因
```

#### 其他

部分代码基于 seven-cow ，功能上有扩展。

API接口有差异，不能替代使用。

