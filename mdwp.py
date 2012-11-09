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


global CONF_FILE, CONF_FILENAME, CONF_DIRECTORY
CONF_FILENAME = '.mdwpconfig'
CONF_DIRECTORY = os.environ['HOME']
CONF_FILE = "%s/%s" % (CONF_DIRECTORY, CONF_FILENAME)


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


def buildXmlRpc(args):
    loaded_conf = loadConfig(CONF_FILE)

    if arg_dict['blogurl']:
        blogurl = args['blogurl']
    elif 'blogurl' in loaded_conf.keys():
        blogurl = loaded_conf['blogurl']
    else:
        blogurl = raw_input('blogurl: ')
    blogurl = '%sxmlrpc.php' % blogurl

    if arg_dict['username']:
        username = args['username']
    elif 'username' in loaded_conf.keys():
        username = loaded_conf['username']
    else:
        username = raw_input('username: ')

    if arg_dict['password']:
        password = args['password']
    elif 'password' in loaded_conf.keys():
        password = loaded_conf['password']
    else:
        password = getpass.getpass('password: ')

    return XmlRpc(blogurl, username, password)


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


def newPost(args):
    xr = buildXmlRpc(args)
    data = codecs.open(args['file'], 'r', 'utf-8').read()
    content = buildContent(data)
    publish = content.pop('publish')
    postid = xr.newPost(content, publish)

    if args['rename']:
        rename(postid, content['title'].replace(' ', '-'), args['file'])

    if postid == True:
        message = "Post the article as postid: %d." % postid
    else:
        message = "failure"

    return message


def editPost(args):
    xr = buildXmlRpc(args)
    postid = int(args['postid'])
    data = codecs.open(args['file'], 'r', 'utf-8').read()
    content = buildContent(data)
    publish = content.pop('publish')
    result = xr.editPost(postid, content, publish)

    if args['rename']:
        rename(postid, content['title'].replace(' ', '-'), args['file'])

    if result == True:
        message = "postid: %d was updated." % postid
    else:
        message = "failure"

    return message


def deletePost(args):
    xr = buildXmlRpc(args)
    postid = int(args['postid'])

    if args['force']:
        yn = raw_input("remove postid: %d? " % postid)
        if not (yn == 'y' or yn == 'yes'):
            return 'cancel'

    result = xr.deletePost(postid)

    if result == True:
        message = "postid: %d was deleted." % postid
    else:
        message = "failure"

    return result


def getList(args):
    xr = buildXmlRpc(args)
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
        if s:
            ss.append("  status: %s" % p['post_status'])
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


def parseConfig(lines):
    d = {}
    r = re.compile(r'(?P<key>[a-z-]+)[\s\t]*=[\s\t]*(?P<val>.+)', re.I)
    for l in lines:
        m = r.match(l)
        if m:
            k = m.groupdict().get('key').strip()
            v = m.groupdict().get('val').strip()
            d[k] = v

    return d


def loadConfig(file):
    if os.path.exists(file):
        with codecs.open(file, 'r', 'utf-8') as f:
            lines = f.readlines()
        conf_dict = parseConfig(lines)

        return conf_dict
    return {}


def saveConfig(file, args):
    conf_dict = {}
    re_dec = re.compile(r'(?P<key>[a-z-]+)[\s\t]*=[\s\t]*(?P<val>.+)', re.I)

    if os.path.exists(file):
        with codecs.open(file, 'r', 'utf-8') as f:
            lines = f.readlines()
        conf_dict = parseConfig(lines)

    if args['blogurl']:
        conf_dict['blogurl'] = args['blogurl']
    if args['username']:
        conf_dict['username'] = args['username']
    if args['password']:
        conf_dict['password'] = args['password']

    conf_strs = []
    for k in conf_dict:
        conf_strs.append("%s = %s\n" % (k, conf_dict[k]))

    with codecs.open(file, 'w', 'utf-8') as f:
        f.writelines(conf_strs)

    return True


if __name__ == '__main__':
    # argument parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_conf = subparsers.add_parser('config')
    parser_conf.add_argument('--blogurl')
    parser_conf.add_argument('--username')
    parser_conf.add_argument('--password')
    saveConfigWrapper = lambda a: saveConfig(CONF_FILE, a)
    parser_conf.set_defaults(func=saveConfigWrapper)

    parser_post = subparsers.add_parser('post')
    parser_post.add_argument('file')
    parser_post.add_argument('-r', '--rename', action='store_true')
    parser_post.add_argument('--blogurl')
    parser_post.add_argument('--username')
    parser_post.add_argument('--password')
    parser_post.set_defaults(func=newPost)

    parser_edit = subparsers.add_parser('update')
    parser_edit.add_argument('postid')
    parser_edit.add_argument('file')
    parser_edit.add_argument('-r', '--rename', action='store_true')
    parser_edit.add_argument('--blogurl')
    parser_edit.add_argument('--username')
    parser_edit.add_argument('--password')
    parser_edit.set_defaults(func=editPost)

    parser_del = subparsers.add_parser('delete')
    parser_del.add_argument('postid')
    parser_del.add_argument('-f', '--force', action='store_true')
    parser_del.add_argument('--blogurl')
    parser_del.add_argument('--username')
    parser_del.add_argument('--password')
    parser_del.set_defaults(func=deletePost)

    parser_list = subparsers.add_parser('list')
    parser_list.add_argument('-n', '--number')
    parser_list.add_argument('-d', '--description', action='store_true')
    parser_list.add_argument('-c', '--categories', action='store_true')
    parser_list.add_argument('-k', '--tags', action='store_true')
    parser_list.add_argument('-s', '--status', action='store_true')
    parser_list.add_argument('--blogurl')
    parser_list.add_argument('--username')
    parser_list.add_argument('--password')
    parser_list.set_defaults(func=getList)

    args = parser.parse_args()
    arg_dict = vars(args)

    result = args.func(arg_dict)

    print(result)
