#! /usr/bin/python
# -*- coding:utf-8 -*-

from __future__ import print_function

import sys
import os
import re
import codecs
import getpass
import xmlrpclib
import argparse
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


def buildContent(data):
    r = re.compile(r'(^---\s*$(?P<yaml>.*?)^---\s*$)?(?P<content>.*)',
                   re.M | re.S)
    match_obj = r.match(data)
    y = yaml.load(match_obj.groupdict().get('yaml'))

    text = match_obj.groupdict().get('content')
    text = gfmToFenced(text)
    text = markdown.markdown(text, extensions=['footnotes', 'codehilite',
                                               'fenced_code'])

    content = {}
    content['title'] = y['title']
    content['description'] = text
    content['categories'] = [y['categories']]
    content['mt_keywords'] = y['tags']

    if y['status'] == 'publish':
        content['publish'] = True
    else:
        content['publish'] = False

    return content


def gfmToFenced(text):
    re_gfm = re.compile(r'^```(?P<lang>[^\n]*?)\n^(?P<body>.*?)^```',
                        re.M | re.S)

    def repFunc(match_obj):
        lang = match_obj.groupdict().get('lang')
        body = match_obj.groupdict().get('body')

        if lang:
            return ("~~~~.%s\n"
                    "%s"
                    "~~~~") % (lang, body)
        else:
            return ("~~~~\n"
                    "%s"
                    "~~~~") % body

    text = re_gfm.sub(repFunc, text)

    return text


def newPost(xr, args):
    data = codecs.open(args['file'], 'r', 'utf-8').read()
    content = buildContent(data)
    publish = content.pop('publish')
    postid = xr.newPost(content, publish)

    if args['rename']:
        rename(postid, content['title'].replace(' ', '-'), args['file'])

    return postid


def editPost(xr, args):
    postid = int(args['postid'])
    data = codecs.open(args['file'], 'r', 'utf-8').read()
    content = buildContent(data)
    publish = content.pop('publish')
    result = xr.editPost(postid, content, publish)

    if args['rename']:
        rename(postid, content['title'].replace(' ', '-'), args['file'])

    return result


def deletePost(xr, args):
    postid = int(args['postid'])

    if args['force'] == False:
        yn = raw_input("remove postid: %d? " % postid)
        if not (yn == 'y' or yn == 'yes'):
            return 'cancel'

    result = xr.deletePost(postid)

    return result


def getList(xr, args):
    num = args['number'] if args['number'] else None
    posts = xr.getRecentPosts(num)

    options = []
    c, t, d = False, False, False
    if args['categories']:
        c = True
    if args['tags']:
        t = True
    if args['description']:
        d = True

    results = []
    for p in posts:
        ss = ["%s: %s" % (p['postid'], p['title'])]
        if c:
            ss.append("  categories: %s" % ', '.join(p['categories']))
        if t:
            ss.append("  tags: %s" % p['mt_keywords'])
        if d:
            ss.append("  %s" % p['descriptions'])
        results.append('\n'.join(ss))
    result = '\n'.join(results)

    return result


def rename(postid, title, file):
    filename = "%s_%s" % (postid, title)
    ext = os.path.splitext(file)[1]
    path = os.path.dirname(file)
    if path:
        dst = "%s/%s%s" % (path, filename, ext)
    else:
        dst = filename

    os.rename(file, dst)


if __name__ == '__main__':
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
            password = getpass.getpass('password: ')
    else:
        blogurl = raw_input('blogurl: ')
        username = raw_input('username: ')
        password = getpass.getpass('password: ')

    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    parser.add_argument('--username')
    parser.add_argument('--password')
    subparsers = parser.add_subparsers()

    parser_post = subparsers.add_parser('post')
    parser_post.add_argument('file')
    parser_post.add_argument('-r', '--rename', action='store_true')
    parser_post.set_defaults(func=newPost)

    parser_edit = subparsers.add_parser('edit')
    parser_edit.add_argument('postid')
    parser_edit.add_argument('file')
    parser_edit.add_argument('-r', '--rename', action='store_true')
    parser_edit.add_argument('-f', '--force', action='store_true')
    parser_edit.set_defaults(func=editPost)

    parser_del = subparsers.add_parser('delete')
    parser_del.add_argument('postid')
    parser_del.add_argument('-f', '--force', action='store_true')
    parser_del.set_defaults(func=deletePost)

    parser_list = subparsers.add_parser('list')
    parser_list.add_argument('-n', '--number')
    parser_list.add_argument('-d', '--description', action='store_true')
    parser_list.add_argument('-c', '--categories', action='store_true')
    parser_list.add_argument('-k', '--tags', action='store_true')
    parser_list.set_defaults(func=getList)

    args = parser.parse_args()
    arg_dict = vars(args)

    ask_pass = False
    ask_user = False
    if arg_dict['url']:
        blogurl = arg_dict['url']
        ask_pass = True
        ask_user = True
    if arg_dict['username']:
        username = arg_dict['username']
        ask_user = False
        ask_pass = True
    if arg_dict['password']:
        password = arg_dict['password']
        ask_pass = False
    if ask_user:
        username = raw_input('username: ')
    if ask_pass:
        password = getpass.getpass('password: ')

    xr = XmlRpc(blogurl, username, password)
    result = args.func(xr, arg_dict)

    print(result)
