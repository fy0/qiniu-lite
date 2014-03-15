from setuptools import setup

def long_description():
    try:
        return open('README.txt').read()
    except IOError:
        return """Yet another qiniu cloud storeage Python SDK
        github: https://github.com/yueyoum/seven-cow
        """

setup(
    name = 'sevencow',
    version = '0.1.3',
    license = 'BSD',
    install_requires = ['requests'],
    py_modules = ['sevencow'],
    author = 'Wang Chao',
    author_email = 'yueyoum@gmail.com',
    url = 'https://github.com/yueyoum/seven-cow',
    description = 'Yet another qiniu cloud storage Python SDK',
    long_description = long_description(),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Topic :: Internet',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
