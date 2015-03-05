
from distutils.core import setup

def description():
    return """A lightweight Qiniu Python SDK.
        github: https://github.com/fy0/qiniu-lite
        """

setup(name='qiniu-lite',
      version='1.0',
      license = 'BSD',
      description=description(),
      author = 'fy',
      author_email = 'fy0@qq.com',
      install_requires = ['requests'],
      url="http://ichiyu.me/qiniu-lite.html",
      packages=['qiniu_lite'],
      classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],

)

