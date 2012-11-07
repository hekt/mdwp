#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import re
import codecs
import xmlrpclib
import yaml
import markdown


class XmlRpc(object):
    def __init__(self, blogurl, username, password, blogid='', appkey=''):
        self.server = xmlrpclib.ServerProxy(blogurl, allow_none=True)
        self.username = username
        self.password = password
        self.blogid = blogid
        self.appkey = appkey

    def getPost(self, postid):
        return self.server.metaWeblog.getRecentPosts(postid, self.username,
                                                     self.password)

    def getRecentPosts(self, numberOfPosts=None):
        if numberOfPosts is not None:
            return self.server.metaWeblog.getRecentPosts(self.blogid,
                                                         self.username,
                                                         self.password,
                                                         numberOfPosts)
        else:
            return self.server.metaWeblog.getRecentPosts(self.blogid,
                                                         self.username,
                                                         self.password)

    def newPost(self, content, publish):
        return self.server.metaWeblog.newPost(self.blogid, self.username,
                                              self.password, content, publish)

    def editPost(self, postid, content, publish):
        return self.server.metaWeblog.editPost(postid, self.username,
                                               self.password, content, publish)

    def deletePost(self, postid, publish=False):
        return self.server.metaWeblog.deletePost(self.appkey, postid,
                                                 self.username, self.password,
                                                 publish)


def post(blogurl, username, password, data):
    r = re.compile(r'(^---\s*$(?P<yaml>.*?)^---\s*$)?(?P<content>.*)',
                   re.M | re.S)
    match_obj = r.match(data)
    y = yaml.load(match_obj.groupdict().get('yaml'))

    if y['status'] == 'publish':
        publish = True
    else:
        publish = False

    text = markdown.markdown(match_obj.groupdict().get('content'),
                             extensions=['footnotes', 'codehilite'])

    content = {}
    content['title'] = y['title']
    content['description'] = text
    content['categories'] = [y['categories']]
    content['mt_keywords'] = y['tags']

    xr = XmlRpc(blogurl, username, password)
    result = xr.newPost(content, publish)
    return result


def edit(blogurl, username, password, postid, data):
    r = re.compile(r'(^---\s*$(?P<yaml>.*?)^---\s*$)?(?P<content>.*)',
                   re.M | re.S)
    match_obj = r.match(data)
    y = yaml.load(match_obj.groupdict().get('yaml'))

    if y['status'] == 'publish':
        publish = True
    else:
        publish = False

    text = markdown.markdown(match_obj.groupdict().get('content'),
                             extensions=['footnotes', 'codehilite'])

    content = {}
    content['title'] = y['title']
    content['description'] = text
    content['categories'] = [y['categories']]
    content['mt_keywords'] = y['tags']
    
    xr = XmlRpc(blogurl, username, password)
    result = xr.editPost(postid, content, publish)
    return result


def delete(blogurl, username, password, postid):
    xr = XmlRpc(blogurl, username, password)
    result = xr.deletePost(postid)
    return result


if __name__ == '__main__':
    if sys.argv[1] in ('post', 'edit', 'delete', 'list'):
        mode = sys.argv[1]
    else:
        sys.exit('invalid option')

    config_path = '%s/.mdwpconfig' % os.environ['HOME']

    if os.path.exists(config_path):
        config = codecs.open(config_path, 'r', 'utf-8').read()
        y = yaml.load(config)
        if 'blogurl' in y.keys():
            blogurl = y['blogurl']
        else:
            blogurl = raw_input('blogurl: ')
        if 'username' in y.keys():
            username = y['username']
        else:
            username = raw_input('username: ')
        if 'password' in y.keys():
            password = y['password']
        else:
            password = raw_input('password: ')
    else:
        blogurl = raw_input('blogurl: ')
        username = raw_input('username: ')
        password = raw_input('password: ')

    if mode == 'post':
        data = codecs.open(sys.argv[2], 'r', 'utf-8').read().encode('utf-8')
        result = post(blogurl, username, password, data)
    elif mode == 'edit':
        postid = sys.argv[2]
        data = codecs.open(sys.argv[3], 'r', 'utf-8').read().encode('utf-8')
        result = edit(blogurl, username, password, postid, data)
    elif mode == 'delete':
        postid = sys.argv[2]
        result = delete(blogurl, username, password, postid)

    print result
