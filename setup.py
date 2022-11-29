#Copyright ReportLab Europe Ltd. 2000-2022
#see _rl_accel-license.txt license.txt for license details
__version__=''
import os, sys, glob, shutil, re, sysconfig, traceback, io, subprocess
from configparser import RawConfigParser
from urllib.parse import quote as urlquote
platform = sys.platform
pjoin = os.path.join
abspath = os.path.abspath
isfile = os.path.isfile
isdir = os.path.isdir
dirname = os.path.dirname
basename = os.path.basename
splitext = os.path.splitext
addrSize = 64 if sys.maxsize > 2**32 else 32
sysconfig_platform = sysconfig.get_platform()

INFOLINES=[]
def infoline(t,
        pfx='#####',
        add=True,
        ):
    bn = splitext(basename(sys.argv[0]))[0]
    ver = '.'.join(map(str,sys.version_info[:3]))
    s = '%s %s-python-%s-%s: %s' % (pfx, bn, ver, sysconfig_platform, t)
    print(s)
    if add: INFOLINES.append(s)

def showTraceback(s):
    buf = io.StringIO()
    print(s,file=buf)
    if verbose>2:
        traceback.print_exc(file=buf)
    for l in buf.getvalue().split('\n'):
        infoline(l,pfx='!!!!!',add=False)

def spCall(cmd,*args,**kwds):
    r = subprocess.call(
            cmd,
            stderr =subprocess.STDOUT,
            stdout = subprocess.DEVNULL if kwds.pop('dropOutput',False) else None,
            timeout = kwds.pop('timeout',3600),
            )
    if verbose>=3:
        infoline('%r --> %s' % (' '.join(cmd),r), pfx='!!!!!' if r else '#####', add=False)
    return r

def specialOption(n,ceq=False):
    v = 0
    while n in sys.argv:
        v += 1
        sys.argv.remove(n)
    if ceq:
        n += '='
        V = [_ for _ in sys.argv if _.startswith(n)]
        for _ in V: sys.argv.remove(_)
        if V:
            n = len(n)
            v = V[-1][n:]
    return v

#defaults for these options may be configured in local-setup.cfg
#[OPTIONS]
#no-download-t1-files=yes
#ignore-system-libart=yes
# if used on command line the config values are not used
mdbg = specialOption('--memory-debug')
verbose = specialOption('--verbose',ceq=True)

if __name__=='__main__':
    pkgDir=dirname(sys.argv[0])
else:
    pkgDir=dirname(__file__)
if not pkgDir:
    pkgDir=os.getcwd()
elif not os.path.isabs(pkgDir):
    pkgDir=abspath(pkgDir)
try:
    os.chdir(pkgDir)
except:
    showTraceback('warning could not change directory to %r' % pkgDir)

from setuptools import setup, Extension

def get_version():
    #determine Version
    #first try source
    fn = pjoin(pkgDir,'src','_rl_accel.c')
    try:
        with open(fn,'r') as _:
            for l in _.readlines():
                if l.startswith('#define'):
                    l = l.split()
                    if l[1]=='VERSION':
                        return eval(l[2],{})
    except:
        raise ValueError('Cannot determine _rl_accel Version')

class config:
    def __init__(self):
        try:
            self.parser = RawConfigParser()
            self.parser.read([pjoin(pkgDir,'setup.cfg'),pjoin(pkgDir,'local-setup.cfg')])
        except:
            self.parser = None

    def __call__(self,sect,name,default=None):
        try:
            return self.parser.get(sect,name)
        except:
            return default
config = config()
def LAM():
    '''return limited api macro'''
    if 'bdist_wheel' in sys.argv or 'build_ext' in sys.argv:
        A = [_ for _ in sys.argv if _.startswith('--py-limited-api=')]
        if A:
            V = A[0][17:]
            if 'bdist_wheel' not in sys.argv:
                for _ in A:
                    sys.argv.remove(_)
            return [('Py_LIMITED_API','0x%02x%02x0000' % (int(V[2]),int(V[3:])))]
    return []
LAM = LAM()

if not mdbg:
    mdbg = config('OPTIONS','memory-debug','0').lower() in ('1','true','yes')

#this code from /FBot's PIL setup.py
def aDir(P, d, x=None):
    if d and isdir(d) and d not in P:
        if x is None:
            P.append(d)
        else:
            P.insert(x, d)

# protection against loops needed. reported by
# Michał Górny &lt; mgorny at gentoo dot org &gt;
# see https://stackoverflow.com/questions/36977259
def findFile(root, wanted, followlinks=True):
    visited = set()
    for p, D, F in os.walk(root,followlinks=followlinks):
        #scan directories to check for prior visits
        #use dev/inode to make unique key
        SD = [].append
        for d in D:
            dk = os.stat(pjoin(p,d))
            dk = dk.st_dev, dk.st_ino
            if dk not in visited:
                visited.add(dk)
                SD(d)
        D[:] = SD.__self__  #set the dirs to be scanned
        for fn in F:
            if fn==wanted:  
                return abspath(pjoin(p,fn))

def showEnv():
    action = -1 if specialOption('--show-env-only') else 1 if specialOption('--show-env') else 0
    if not action: return
    print('+++++ setup.py environment')
    print('+++++ sys.version = %s' % sys.version.replace('\n',''))
    import platform
    for k in sorted((_ for _ in dir(platform) if not _.startswith('_'))):
        try:
            v = getattr(platform,k)
            if isinstance(v,(str,list,tuple,bool)):
                v = repr(v)
            if callable(v) and v.__module__=='platform':
                v = repr(v())
            else:
                continue
        except:
            v = '?????'
        print('+++++ platform.%s = %s' % (k,v))
    print('--------------------------')
    for k, v in sorted(os.environ.items()):
        print('+++++ environ[%s] = %r' % (k,v))
    print('--------------------------')
    if action<0:
        sys.exit(0)

def main():
    showEnv()
    #test to see if we've a special command

    debug_compile_args = []
    debug_link_args = []
    debug_macros = LAM
    debug = int(os.environ.get('RL_DEBUG','0'))
    if debug:
        if sys.platform == 'win32':
            debug_compile_args=['/Zi']
            debug_link_args=['/DEBUG']
        if debug>1:
            debug_macros.extend([('RL_DEBUG',debug), ('ROBIN_DEBUG',None)])
    if mdbg:
        debug_macros.extend([('MEMORY_DEBUG',None)])

    LIBRARIES=[]
    EXT_MODULES = []

    infoline( '================================================')
    infoline( 'Attempting build of _rl_accel')
    infoline( 'extensions from src/_rl_accel.c')
    infoline( '================================================')
    EXT_MODULES += [
                Extension( '_rl_accel',
                            [pjoin('src','_rl_accel.c')],
                            include_dirs=[],
                        define_macros=[]+debug_macros,
                        library_dirs=[],
                        libraries=[], # libraries to link against
                        extra_compile_args=debug_compile_args,
                        extra_link_args=debug_link_args,
                        ),
                    ]

    try:
        setup(
            name="rl_accel",
            version=get_version(),
            license="BSD license (see LICENSE.txt for details), Copyright (c) 2000-2022, ReportLab Inc.",
            description="Acclerator for ReportLab",
            long_description="""This is an accelerator module for the ReportLab Toolkit Open Source Python library for generating PDFs and graphics.""",
            author="Andy Robinson, Robin Becker, the ReportLab team and the community",
            author_email="reportlab-users@lists2.reportlab.com",
            url="http://www.reportlab.com/",
            packages=[],
            package_data = {'': ('_rl_accel-license.txt',)},
            ext_modules =   EXT_MODULES,
            classifiers = [
                'Development Status :: 5 - Production/Stable',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: BSD License',
                'Topic :: Printing',
                'Topic :: Text Processing :: Markup',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.7',
                'Programming Language :: Python :: 3.8',
                'Programming Language :: Python :: 3.9',
                'Programming Language :: Python :: 3.10',
                'Programming Language :: Python :: 3.11',
                ],
            
            #this probably only works for setuptools, but distutils seems to ignore it
            install_requires=[],
            python_requires='>=3.7,<4',
            extras_require={
                },
            )
        print()
        print('########## SUMMARY INFO #########')
        print('\n'.join(INFOLINES))
    finally:
        pass

if __name__=='__main__':
    main()
