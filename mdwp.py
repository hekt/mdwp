#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
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

    def newPost(self):
        return self.server.metaWeblog.newPost(self.blogid, self.username, 
                                              self.password, data, status)

    def editPost(self, postid, content, publish=False):
        return self.server.metaWeblog.editPost(postid, self.username, 
                                               self.password, content, publish)

    def deletePost(self, postid, publish=False):
        return self.server.metaWeblog.deletePost(self.appkey, postid, self.username, 
                                                 self.password, publish)





# class (object)
# r = re.compile(r'(^---\s*$(?P<yaml>.*?)^---\s*$)?(?P<content>.*)',
#                re.M | re.S)
# post_file = open(sys.argv[1], 'r').read()
# match_dict = r.match(post_file).groupdict()
# yaml_data = yaml.load(self.match_dict.get('yaml'))
# md_data = markdown.markdown(self.match_dict.get('content'),
#                             extensions=['footnotes', 'codehilite'])

# blogurl = 'http://localhost:8888/wordpress/xmlrpc.php'
# username = self.username
# password = self.password
# server = xmlrpclib.ServerProxy(blogurl, allow_none=True)

# if getYAML['status'] == 'publish':
#         status = '1'
# else: status = '0'
        
# data = {}
# data['title'] = getYAML['title']
# data['description'] = newPost
# data['categories'] = [getYAML['categories']]
# data['mt_keywords'] = getYAML['tags']
