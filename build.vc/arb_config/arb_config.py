﻿'''
Set up Visual Sudio to build a specified MPIR configuration

Copyright (C) 2011, 2012, 2013, 2014 Brian Gladman
'''

from operator import itemgetter
from os import scandir, walk, unlink, makedirs, remove
from os.path import join, split, splitext, isdir, exists
from os.path import dirname, abspath, relpath, realpath, normpath
from copy import deepcopy
from sys import argv, exit, path
from filecmp import cmp
from shutil import copy
from re import compile, search
from collections import defaultdict
from uuid import uuid4
from time import sleep

from _msvc_filters import gen_filter
from _msvc_project import Project_Type, gen_vcxproj
from _msvc_solution import msvc_solution

vs_version = 19
if len(argv) > 1:
  vs_version = int(argv[1])

project_name = 'arb'
solution_name = project_name + '.sln'

script_dir = dirname(realpath(__file__))
build_dir_name = 'build.vs{0:d}'.format(vs_version)
build_root_dir = abspath(join(script_dir, '..\\..\\' + build_dir_name))
build_aux_dir = abspath(join(script_dir, '..\\..\\' + 'build.vc'))
path.append(build_root_dir)
from version_info import vs_info

# add user choice (duplicate in _msvc_project.py)
flib_type = 'single' # ('gc', 'reentrant', 'single')

# The path to arb, solution and project directories
arb_dir = abspath(join(script_dir, '../../'))
solution_dir = abspath(join(arb_dir, build_dir_name))

# for script debugging
debug = False
# what to build
build_lib = True
build_dll = True
build_tests = False

# copy from file ipath to file opath but avoid copying if
# opath exists and is the same as ipath (this is to avoid
# triggering an unecessary rebuild).

def write_f(ipath, opath):
  if exists(ipath) and not isdir(ipath):
    if exists(opath):
      if isdir(opath) or cmp(ipath, opath):
        return
    copy(ipath, opath)

ignore_dirs = ( '.git', '.vs', 'doc', 'examples', 'lib', 'exe', 'dll', 'build', 'build.vc', 'out', 'profile')
req_extns = ( '.h', '.c', '.cc', '.cpp' )

def find_src(path):

  c, h, t, = [], [], []
  for root, dirs, files in walk(path):
    if 'template' in root:
      continue
    _, _t = split(root)
    if _t in ignore_dirs:
      continue
    if build_dir_name in root:
      for di in list(dirs):
        dirs.remove(di)
    for di in list(dirs):
      if di in ignore_dirs or search(r'\.v(c|s)\d+', di):
        dirs.remove(di)
    relp = relpath(root, arb_dir)
    if relp == '.':
      relp = ''
    for f in files:
      n, x = splitext(f)
      if x not in req_extns:
        continue
      pth, leaf = split(root)
      fp = join(relp, f)
      if leaf == 'test':
        p2, l2 = split(pth)
        l2 = '' if l2 == 'arb' else l2
        t += [(l2, fp)]
      elif x == '.c':
        c += [(leaf, fp)]
      elif x == '.h':
        h += [fp]

  for x in (c, h, t):
    x.sort()
  return (c, h, t)

s_sym = r'([_a-zA-Z][_a-zA-Z0-9]*)'
dec = '^(?:' + s_sym + '\s+)?' + s_sym + '\('
re_dec = compile(dec)
re_end = compile('\s*\);\s*$')

# crude parser to detect function declarations in
# arb header files (no longer needed but left in
# place in case this changes).

def strip_static_inline(lines, pos, lth):
  p0 = pos
  m = re_end.search(lines[pos])
  pos += 1
  if m:
    return pos
  level = 0
  while pos < lth:
    line = (lines[pos].replace('\n', ' ')).strip()
    m = re_end.search(lines[pos])
    if not level and (m or not line or pos > p0 + 5) or pos >= lth:
      return pos + 1
    level += line.count('{') - line.count('}')
    pos += 1
  return pos

def parse_hdrs(h):
  d = defaultdict(list)
  for hf in h:
    lines = open(join(arb_dir, hf), 'r').readlines()
    pos, n_lines = 0, len(lines)
    line_buf = ''
    in_dec = 0
    while pos < n_lines:
      if in_dec == 0:
        line_buf = ''
      line = (lines[pos].replace('\n', ' ')).strip()
      if not line:
        pos += 1
        continue
      if line.startswith('#define'):
        while line.endswith('\\') and pos < n_lines:
          pos += 1
          line = (lines[pos].replace('\n', ' ')).strip()
        pos += 1
        continue
      if 'INLINE' in line.upper():
        pos = strip_static_inline(lines, pos, n_lines)
        in_dec = 0
        continue
      if not in_dec:
        m = re_dec.search(line)
        if m:
          line_buf += line + ' '
          mm = re_end.search(line)
          if mm:
            pos += 1
            print(m.group(2))
            d[hf] += [(pos, m.group(2), line_buf)]
            in_dec = 0
            continue
          in_dec += 1
      else:
        line_buf += line
        mm = re_end.search(line)
        if mm:
          if in_dec < 5:
            d[hf] += [(pos - in_dec + 1, m.group(2), line_buf)]
          in_dec = 0
        else:
          in_dec += 1
      pos += 1
  return d

def write_hdrs(h):
  d = parse_hdrs(h)
  hdr_dir = join(arb_dir, 'win_hdrs')
  if not exists(hdr_dir):
    makedirs(hdr_dir)

  for hf in sorted(d.keys()):
    out_name = hf.replace('build.vc14\\', '')
    inf = open(join(arb_dir, hf), 'r')
    outf = open(join(arb_dir, join(hdr_dir, out_name)), 'w')
    lines = inf.readlines()
    for n, _p, _d in d[hf]:
      lines[n - 1] = 'ARB_DLL ' + lines[n - 1]
    outf.writelines(lines)
    inf.close()
    outf.close()

def write_def_file(name, h):
  d = parse_hdrs(h)
  lines = ['LIBRARY ' + name + '\n', 'EXPORTS' + '\n']
  for hf in sorted(d.keys()):
    for _n, sym, _d in d[hf]:
      lines += ['    ' + sym + '\n']
  with open(join(solution_dir, name + '.def'), 'w') as outf:
    outf.writelines(lines)

# end of parser code

# add project files to the solution

c, h, t = find_src(arb_dir)

# write_hdrs(h)

# input any existing projects in the solution (*.sln) file
solc = msvc_solution(abspath(join(solution_dir, solution_name)))

write_f(r'..\..\..\flint\build.vc\config.h', r'..\..\..\flint\config.h')

if build_lib:
  # set up LIB build
  proj_name = 'lib_arb'
  vcx_name = 'lib_arb'
  vcx_path = abspath(join(solution_dir, vcx_name, vcx_name + '.vcxproj'))
  gen_filter(vcx_path + '.filters', arb_dir, h, c, [], '12.0')
  guid = solc.get_project_guid(vcx_name, vcx_path)
  mode = ('Win32', 'x64')
  inc_dirs = r'..\..\;..\..\build.vc;..\..\..\mpir\lib\$(IntDir);..\..\..\mpfr\lib\$(IntDir);..\..\..;..\..\..\pthreads\lib\$(IntDir);'
  link_libs = r'..\..\..\mpir\lib\$(IntDir)mpir.lib;..\..\..\mpfr\lib\$(IntDir)mpfr.lib;..\..\..\flint\lib\$(IntDir)lib_flint.lib;..\..\..\pthreads\lib\$(IntDir)pthreads.lib;'
  gen_vcxproj(vcx_path, arb_dir, proj_name, guid, mode, Project_Type.LIB, flib_type, True, True, True, h, c, inc_dirs, link_libs, vs_info)
  solc.add_project('', vcx_name, vcx_path, guid, mode)

if build_dll:
  # set up DLL build

  # no longer needed
  # write_def_file('dll_arb', h)

  proj_name = 'dll_arb'
  vcx_name = 'dll_arb'
  vcx_path = abspath(join(solution_dir, vcx_name, vcx_name + '.vcxproj'))
  gen_filter(vcx_path + '.filters', arb_dir, h, c, [], '12.0')
  guid = solc.get_project_guid(vcx_name, vcx_path)
  mode = ('Win32', 'x64')
  inc_dirs = r'..\..\;..\..\build.vc;..\..\..\mpir\dll\$(IntDir);..\..\..\mpfr\dll\$(IntDir);..\..\..\;..\..\..\pthreads\dll\$(IntDir);'
  link_libs = r'..\..\..\mpir\dll\$(IntDir)mpir.lib;..\..\..\mpfr\dll\$(IntDir)mpfr.lib;..\..\..\flint\dll\$(IntDir)dll_flint.lib;..\..\..\pthreads\dll\$(IntDir)pthreads.lib;'
  gen_vcxproj(vcx_path, arb_dir, proj_name, guid, mode, Project_Type.DLL, flib_type, True, True, True, h, c, inc_dirs, link_libs, vs_info)
  solc.add_project('', vcx_name, vcx_path, guid, mode)

solc.write_solution(vs_info)

def gen_test(sol, solf, test_name, directory, proj_dir, name, c_file):
  # set up LIB build
  proj_name = vcx_name = test_name[2:]
  vcx_path = abspath(join(solution_dir, directory, name + '_' + vcx_name, vcx_name + '.vcxproj'))
  gen_filter(vcx_path + '.filters', solution_dir, [], [('', c_file)], [], '12.0')
  guid = sol.get_project_guid(vcx_name, vcx_path)
  mode = ('Win32', 'x64')
  inc_dirs = r'..\..\;..\..\..\;..\..\..\..\mpir\lib\$(IntDir);..\..\..\..\mpfr\lib\$(IntDir);..\..\..\;..\..\..\..\pthreads\lib\$(IntDir);'
  link_libs = r'..\..\..\lib\$(IntDir)lib_arb.lib;..\..\..\..\mpir\lib\$(IntDir)mpir.lib;..\..\..\..\mpfr\lib\$(IntDir)mpfr.lib;..\..\..\..\flint\lib\$(IntDir)lib_flint.lib;..\..\..\..\pthreads\lib\$(IntDir)pthreads.lib;'
  gen_vcxproj(vcx_path, arb_dir, test_name, guid, mode, Project_Type.APP, flib_type, False, False, False, [], [('', c_file)], inc_dirs, link_libs, vs_info)
  sol.add_project(solf, vcx_name, vcx_path, guid)

def gen_tests(sln_name, directory, proj_dir, c_files):
  sn = sln_name[:sln_name.rfind('.')]
  for cnt, (name, fpath) in enumerate(c_files):
    soln = sn + str(cnt // 100 + 1) + '.sln'
    if cnt % 100 == 0:
      print(soln)
      solc = msvc_solution(abspath(join(solution_dir, directory, soln)))
    print('  ', cnt, name, fpath)
    _, t = split(fpath)
    if t[:2] not in ('t-', 'p-'):
      continue
    p_name = t.replace('.c', '')
    gen_test(solc, name, p_name, directory, proj_dir, name, fpath)
    if cnt % 100 == 99:
      solc.write_solution(vs_info)
  if cnt % 100:
    solc.write_solution(vs_info)

if build_tests:
  gen_tests('arb-tests.sln', 'arb-tests', 'tests', t)

if debug:
  print('\nC files')
  for d in c:
    print('  ', d)
  print('\nC header files')
  for d in h:
    print('  ', d)
  print('\nC++ files')
  for d in cx:
    print('  ', d)
  print('\nC++ header files')
  for d in hx:
    print('  ', d)
  print('\nC Test files')
  for d in t:
    print('  ', d)
  print('\nC++ Test files')
  for d in tx:
    print('  ', d)
  print('\nProfile files')
  for d in p:
    print('  ', d)
