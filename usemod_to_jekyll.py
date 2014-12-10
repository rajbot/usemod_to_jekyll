#!/usr/bin/env python

"""
Convert a usemod wiki to agit-backed jekyll site.

You will need to add git usernames to the dict below

Usage: ./usemod_to_jekyll.py usemod/wikidb jekyll/_posts

You can run doctests by running `py.test --doctest-modules -v`
"""

#stdlib packages
import datetime
import glob
import io
import os
import re
import subprocess
import sys
from os.path import join

#installed packages
import yaml

git_users = {
    'Raj': 'rajbot <raj@'+'archive.org>',
    'Krazykringle': 'mikemccabe <mccabe@'+'archive.org>',
    'McCabe': 'mikemccabe <mccabe@'+'archive.org>',
    'Dasfoo': 'dasfoo <dasfoo@'+'yahoo.com>',
    'Mang': 'Michael Ang <mang@'+'archive.org>',
    'Sasha': 'sasha <sasha@'+'mortalspaces.com>',
    'Richard': 'richard <richard@'+'lee.name>',
    'Pabaphree': 'pabaphree <pabaphree@'+'gmail.com>',
    'DaRaNCH': 'tronix <tronix@'+'ranchtronix.org>',
    'Nix': 'nix <nix@'+'nixweb.com>',
    'Saz': 'saz <nurzboogie@'+'yahoo.com>',
    'Sazz': 'saz <nurzboogie@'+'yahoo.com>',
    'Test': 'tronix <tronix@'+'ranchtronix.org>',
    'Mccabe': 'mikemccabe <mccabe@'+'archive.org>',
    'JesseHammons': 'jesse <jesse@'+'zaggle.org>',
    'Foo': 'dasfoo <dasfoo@'+'yahoo.com>',
}
default_user = 'DaRaNCH'


# convert_usemod_to_jekyll()
#_________________________________________________________________________________________
def convert_usemod_to_jekyll(input_dir, output_dir):
    #process_keep_file('/tmp/rtx2/rtxwikiData/keep/B/BurningMang.kp', output_dir)
    #process_page_file('/tmp/rtx2/rtxwikiData/page/B/BurningMang.db', output_dir)

    #process_keep_file('/tmp/rtx2/rtxwikiData/keep/M/MuZiq.kp', output_dir)
    #process_page_file('/tmp/rtx2/rtxwikiData/page/M/MuZiq.db', output_dir)

    process_dir(join(input_dir, 'keep'), output_dir, keep_dir=True)
    process_dir(join(input_dir, 'page'), output_dir, keep_dir=False)


# process_dir()
#_________________________________________________________________________________________
def process_dir(input_dir, output_dir, keep_dir=False):
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            print 'processing', join(root, file)
            if keep_dir:
                process_keep_file(join(root, file), output_dir)
            else:
                process_page_file(join(root, file), output_dir)



# process_keep_file()
#_________________________________________________________________________________________
def process_keep_file(file, output_dir):
    assert file.endswith('.kp')
    contents = open(file).read()
    #print contents

    fs = "\xb3"
    fs1 = fs + "1"
    fs2 = fs + "2"
    fs3 = fs + "3"

    versions = contents.split(fs1)
    assert versions[0] == ''
    if len(versions) < 2:
        return

    first_page = get_dict(versions[1], fs2)
    timestamp = first_page['tscreate']
    dt = datetime.datetime.fromtimestamp(float(timestamp))
    output_file, title = get_jekyll_filename(dt, file)
    assert not os.path.exists(output_file)

    category = get_category(file)

    for version in versions[1:]:
        page = get_dict(version, fs2)
        data = get_dict(page['data'], fs3)
        timestamp = page['ts']
        username = page['username']
        if username == '':
            username = default_user
        dt = datetime.datetime.fromtimestamp(float(timestamp))

        write_post(output_dir, output_file, title, dt, username, category, data['text'])

        print ' wrote revision', page['revision']
        print ' user:', username, ' timestamp:', timestamp, ' date:', dt.isoformat().replace('T', ' '), '\n'



# process_page_file()
#_________________________________________________________________________________________
def process_page_file(file, output_dir):
    contents = open(file).read()
    #print contents

    fs = "\xb3"
    fs1 = fs + "1"
    fs2 = fs + "2"
    fs3 = fs + "3"

    page = get_dict(contents, fs1)
    create_timestamp = page['tscreate']
    revision = int(page['revision'])
    create_dt = datetime.datetime.fromtimestamp(float(create_timestamp))

    output_file, title = get_jekyll_filename(create_dt, file)
    if revision != 1:
        assert os.path.exists(join(output_dir, output_file))

    section = get_dict(page['text_default'], fs2)
    username = section['username']
    if username == '':
        username = default_user

    timestamp = section['ts']
    dt = datetime.datetime.fromtimestamp(float(timestamp))

    data = get_dict(section['data'], fs3)
    text = data['text']

    category = get_category(file)

    write_post(output_dir, output_file, title, dt, username, category, data['text'])

    print ' wrote revision', revision
    print ' user:', username, ' timestamp:', timestamp, ' date:', dt.isoformat().replace('T', ' '), '\n'


# get_dict()
#_________________________________________________________________________________________
def get_dict(buf, fs):
    s = buf.split(fs)
    keys = s[::2]
    vals = s[1::2]
    assert len(keys) == len(vals)
    return dict(zip(keys, vals))


# get_jekyll_filename()
#_________________________________________________________________________________________
def get_jekyll_filename(dt, usemod_file):
    assert usemod_file.endswith('.kp') or usemod_file.endswith('.db')
    title = os.path.basename(usemod_file)[:-3]
    output_file = '{d}-{t}.md'.format(d=dt.strftime('%Y-%m-%d'), t=title)
    return output_file, title


# get_category()
#_________________________________________________________________________________________
def get_category(file):
    category = None
    m = re.search(r'/(?:page|keep)/[A-Z]/(.+)/'+os.path.basename(file), file)
    if m:
        category = m.group(1)
    return category


# write_post()
#_________________________________________________________________________________________
def write_post(output_dir, output_file, title, dt, username, category, txt):
    filename = join(output_dir, output_file)
    frontmatter = {'layout': 'post',
                   'title': title,
                   'date': dt.isoformat().replace('T', ' '),
                   'author': username,
                  }

    if category is not None:
        frontmatter['category'] = category

    f = io.open(filename, 'w', encoding='utf-8')

    f.write(u'---\n')
    yaml.dump(frontmatter, f, default_flow_style=False)
    f.write(u'---\n\n')

    unicode_txt = txt.decode('iso-8859-1')
    f.write(usemod_to_markdown(unicode_txt))
    f.close()

    git_author = git_users[username]
    orig_dir = os.getcwd()
    os.chdir(os.path.expanduser(output_dir))
    subprocess.check_call(['git', 'add', output_file])
    cmd = ['git', 'commit', '--author', git_author, '--date', dt.isoformat(), '-m', 'Migrating from UseMod wiki', output_file]
    #print cmd
    subprocess.check_call(cmd)
    os.chdir(orig_dir)


# usemod_to_markdown()
#_________________________________________________________________________________________
def usemod_to_markdown(input_txt):
    """regex-based usemod syntax conversion...

    we have copied data from usemod's $UploadDir to image_dir

    #images
    >>> print(usemod_to_markdown('upload:ambamb.jpg<br>').strip())
    ![ambamb.jpg]({{ site.baseurl }}/images/ambamb.jpg)<br>

    >>> print(usemod_to_markdown('upload:butterfly-ports.png<br>').strip())
    ![butterfly-ports.png]({{ site.baseurl }}/images/butterfly-ports.png)<br>


    #headers
    >>> print(usemod_to_markdown('= Ambience Ambulance =').strip())
    # Ambience Ambulance


    #links
    >>> print(usemod_to_markdown('[http://example.com Example Link]').strip())
    [Example Link](http://example.com)


    #bare links
    >>> print(usemod_to_markdown('http://example.com - example link').strip())
    [http://example.com](http://example.com) - example link

    >>> print(usemod_to_markdown('bare link with period https://example.com.').strip())
    bare link with period [https://example.com](https://example.com).

    >>> print(usemod_to_markdown('trailing slash http://example.com/').strip())
    trailing slash [http://example.com/](http://example.com/)


    #internal links
    >>> print(usemod_to_markdown('[[Internal Link]] [[Link Two]]').strip())
    [Internal Link](Internal_Link.html) [Link Two](Link_Two.html)


    #camelcase links
    >>> print(usemod_to_markdown('CamelCase').strip())
    [CamelCase](CamelCase.html)

    >>> print(usemod_to_markdown('[[HeartOfPork]]').strip())
    [HeartOfPork](HeartOfPork.html)

    >>> print(usemod_to_markdown('MoSFeTz').strip())
    [MoSFeTz](MoSFeTz.html)


    #fix lists that don't have required whitespace after asterisk
    >>> x = '''list:\\n*one\\n*two\\n*three'''
    >>> print(usemod_to_markdown(x).strip())
    list:
    <BLANKLINE>
    * one
    * two
    * three

    >>> x = '''list:\\n\\n*one\\n*two\\n*three'''
    >>> print(usemod_to_markdown(x).strip())
    list:
    <BLANKLINE>
    * one
    * two
    * three


    #fix pre blocks that start with a single space
    >>> x = '''### djlog\\n 2006/07/30 - FnF 10 Year Anniversary\\n 2006/07/03 - Black Rock July 4th\\n'''
    >>> print(usemod_to_markdown(x).strip())
    ### djlog
        2006/07/30 - FnF 10 Year Anniversary
        2006/07/03 - Black Rock July 4th

    """

    image_dir = 'images'
    output_txt = ''

    for line in input_txt.splitlines():
        #images
        line = re.sub(r'upload:(\S*\.(?:JPG|PNG))', r'![\1]({{ site.baseurl }}/images/\1)', line, flags=re.I)

        #headers
        line = re.sub(r'^=\s+(.*?)\s+=\s*$', r'# \1', line)
        line = re.sub(r'^==\s+(.*?)\s+==\s*$', r'## \1', line)
        line = re.sub(r'^===\s+(.*?)\s+===\s*$', r'### \1', line)
        line = re.sub(r'^====\s+(.*?)\s+====\s*$', r'## \1', line)

        #links
        line = re.sub(r'\[(https?.*?)\s+(.+?)\]', r'[\2](\1)', line)

        #bare links
        line = re.sub(r'(\s+|^)(https?://\S+?)(\.?\s+|\.?$)', r'\1[\2](\2)\3', line)

        #internal links
        def make_link(m):
            return '[{t}]({l}.html)'.format(t=m.group(1), l=m.group(1).replace(' ', '_'))
        line = re.sub(r'\[\[(.*?)\]\]', make_link, line)

        #camelcase links
        line = re.sub(r'(\s|^)([A-Z][a-z]+[A-Z]+[a-z].*?)(\s|$)', r'\1[\2](\2.html)\3', line)


        #fix lists that don't have required whitespace after asterisk
        line = re.sub(r'^\*(\S)', r'* \1', line)

        #fix pre blocks that start with a single space
        line = re.sub(r'^ (\S)', r'    \1', line)

        output_txt += line + '\n'

    #fix lists that don't have required blank line above

    output_txt = re.sub(r'^(?!\*)(.*\S.*)\n\*', r'\1\n\n*', output_txt, flags=re.MULTILINE)

    return output_txt




# main()
#_________________________________________________________________________________________
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit('Usage: ./usemod_to_jekyll usemod/wikiData/page jekyll/_posts')
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]


    if not os.path.exists(input_dir):
        sys.exit('UseMod wiki data directory not found')

    if not os.path.exists(join(input_dir, 'page')):
        sys.exit('UseMod page directory not found')

    if not os.path.exists(join(input_dir, 'keep')):
        sys.exit('UseMod keep directory not found')

    if not os.path.exists(output_dir):
        sys.exit('The Jekyll _posts directory was not found')

    if len(glob.glob(join(output_dir, '*'))) > 0:
        #print glob.glob(join(output_dir, '*'))
        sys.exit('output directory should be empty')


    convert_usemod_to_jekyll(input_dir, output_dir)
