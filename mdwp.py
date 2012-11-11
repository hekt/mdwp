#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import re
import codecs
import getpass
import xmlrpclib
import argparse
import yaml
import markdown


global CONF_FILE
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


class Parser(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        help_rename = 'rename the file as "POSTID_TITLE.ext" when task succeed'
        help_number = 'the number of articles to display'
        help_description = 'display discriptions'
        help_categories = 'dispaly categories'
        help_tags = 'display tags'
        help_status = 'display statuses'

        # only as `parents`
        common_bloginfo = argparse.ArgumentParser(add_help=False)
        common_bloginfo.add_argument('--blogurl', metavar='URL')
        common_bloginfo.add_argument('--username')
        common_bloginfo.add_argument('--password')
        common_rename = argparse.ArgumentParser(add_help=False)
        common_rename.add_argument('-r', '--rename', action='store_true',
                                   help=help_rename)

        parser_conf = subparsers.add_parser('config', help='save login info',
                                            parents=[common_bloginfo])
        parser_conf.set_defaults(func=self.saveConfig)

        parser_post = subparsers.add_parser('post', help='new post',
                                            parents=[common_bloginfo,
                                                     common_rename])
        parser_post.add_argument('file')
        parser_post.set_defaults(func=self.newPost)

        parser_edit = subparsers.add_parser('update', help='update a post',
                                            parents=[common_bloginfo,
                                                     common_rename])
        parser_edit.add_argument('postid')
        parser_edit.add_argument('file')
        parser_edit.set_defaults(func=self.editPost)

        parser_del = subparsers.add_parser('delete',
                                           help='move to trash a post',
                                           parents=[common_bloginfo])
        parser_del.add_argument('postid')
        parser_del.set_defaults(func=self.deletePost)

        parser_list = subparsers.add_parser('list',
                                            help='display recent posts',
                                            parents=[common_bloginfo])
        parser_list.add_argument('-n', '--number', metavar='N',
                                 help=help_number)
        parser_list.add_argument('-d', '--description', action='store_true',
                                 help=help_description)
        parser_list.add_argument('-c', '--categories', action='store_true',
                                 help=help_categories)
        parser_list.add_argument('-k', '--tags', action='store_true',
                                 help=help_tags)
        parser_list.add_argument('-s', '--status', action='store_true',
                                 help=help_status)
        parser_list.set_defaults(func=self.getList)

        self.parser = parser
        self.parser_post = parser_post
        self.parser_edit = parser_edit
        self.parser_del = parser_del
        self.parser_list = parser_list
        self.parser_conf = parser_conf

        self.status = True
        self.message = ''
        self.mode = ''

    def newPost(self, args):
        xr = Common().buildXmlRpc(args)
        data = codecs.open(args['file'], 'r', 'utf-8').read()
        content = Common().buildContent(data)
        publish = content.pop('publish')
        postid = xr.newPost(content, publish)

        if args['rename']:
            basename = "%s_%s" % (postid, content['title'])
            SysManage().renameFile(args['file'], basename)

        return "the article was posted as postid: %s." % postid

    def editPost(self, args):
        xr = Common().buildXmlRpc(args)
        postid = int(args['postid'])
        data = codecs.open(args['file'], 'r', 'utf-8').read()
        content = Common().buildContent(data)
        publish = content.pop('publish')
        result = xr.editPost(postid, content, publish)

        if args['rename']:
            basename = "%s_%s" % (postid, content['title'])
            SysManage().renameFile(args['file'], basename)

        return "postid: %d was updated." % postid

    def deletePost(self, args):
        xr = Common().buildXmlRpc(args)
        postid = int(args['postid'])
        result = xr.deletePost(postid)

        return "postid: %d was moved to trash." % postid

    def getList(self, args):
        xr = Common().buildXmlRpc(args)
        num = args['number'] if args['number'] else None
        posts = xr.getRecentPosts(num)

        options = []
        categories, tags, status, description = False, False, False, False
        if args['categories']:
            categories = True
        if args['tags']:
            tags = True
        if args['status']:
            status = True
        if args['description']:
            description = True

        results = []
        for p in posts:
            ss = ["%s: %s" % (p['postid'], p['title'])]
            if categories:
                ss.append("  categories: %s" % ', '.join(p['categories']))
            if tags:
                ss.append("  tags: %s" % p['mt_keywords'])
            if status:
                ss.append("  status: %s" % p['post_status'])
            if description:
                ss.append("  %s" % p['description'])
            results.append('\n'.join(ss))

        return '\n'.join(results)

    def saveConfig(self, args):
        options = ('blogurl', 'username', 'password')
        conf_dict = {}

        no_opt = True
        for i in options:
            if args[i]:
                conf_dict[i] = args[i]
                no_opt = False

        if no_opt:
            self.parser_conf.error("config takes at least one option.")

        SysManage().saveConfigFile(CONF_FILE, conf_dict)

        return "saved."


class Common(object):
    def buildContent(self, data):
        r = re.compile(r'(^---\s*$(?P<yaml>.*?)^---\s*$)?(?P<content>.*)',
                       re.M | re.S)
        match_obj = r.match(data)
        y = yaml.load(match_obj.groupdict().get('yaml'))

        text = match_obj.groupdict().get('content')
        text = self.gfmToFenced(text)
        text = markdown.markdown(text, extensions=['footnotes', 'codehilite',
                                                   'fenced_code'])

        content = {}
        content['title'] = y['title']
        content['description'] = text
        content['categories'] = map(lambda s: s.strip(),
                                    y['categories'].split(','))
        content['mt_keywords'] = map(lambda s: s.strip(),
                                     y['tags'].split(','))

        if y['status'] == 'publish':
            content['publish'] = True
        else:
            content['publish'] = False

        return content

    def buildXmlRpc(self, args):
        loaded_conf = self.loadConfig(CONF_FILE)

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

    def gfmToFenced(self, text):
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

        return re_gfm.sub(repFunc, text)

    def loadConfig(self, file):
        if os.path.exists(file):
            with codecs.open(file, 'r', 'utf-8') as f:
                lines = f.readlines()
            conf_dict = self.parseConfig(lines)
            return conf_dict
        return {}

    def parseConfig(self, lines):
        d = {}
        r = re.compile(r'(?P<key>[a-z-]+)[\s\t]*=[\s\t]*(?P<val>.+)', re.I)
        for l in lines:
            m = r.match(l)
            if m:
                k = m.groupdict().get('key').strip()
                v = m.groupdict().get('val').strip()
                d[k] = v
        return d


class SysManage(object):
    def saveConfigFile(self, file, conf_dict):
        re_dec = re.compile(r'(?P<key>[a-z-]+)[\s\t]*=[\s\t]*(?P<val>.+)',
                            re.I)

        if os.path.exists(file):
            with codecs.open(file, 'r', 'utf-8') as f:
                lines = f.readlines()
            current_conf = Common.parseConfig(lines)

        for k in conf_dict:
            current_conf[k] = conf_dict[k]

        conf_strs = []
        for k in current_conf:
            conf_strs.append("%s = %s\n" % (k, current_conf[k]))

        with codecs.open(file, 'w', 'utf-8') as f:
            f.writelines(conf_strs)

    def renameFile(self, file, basename):
        ext = os.path.splitext(file)[1]
        path = os.path.dirname(file)
        if path:
            dst = "%s/%s%s" % (path, basename, ext)
        else:
            dst = "%s%s" % (basename, ext)
        os.rename(file, dst)


if __name__ == '__main__':
    p = Parser()
    args = p.parser.parse_args()
    arg_dict = vars(args)
    result = args.func(arg_dict)

    print(result['message'])
