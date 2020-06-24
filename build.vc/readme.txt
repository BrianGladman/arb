Building ARB with Microsoft Visual Studio
-------------------------------------------------

Building ARB with Microsoft Visual Studio requires Visual
Visual Studio 2015 Community (or higher version) and:

    a) an installed version of Python 3
    b) an installed version of Python Tools for 
       Visual Studio (http://pytools.codeplex.com/)

Obtain ARB either as a released distribution or clone it using
GIT from:

    git@github.com:BrianGladman/arb.git

ARB depends on the MPIR, MPFR and PTHREADS libraries that have
to be installed and built using Visual Studio before ARB can
be built.  The application directories are assumed to be in the
same root directory with the names and layouts:
   
    mpir
       lib
       dll
    mpfr  
       lib
       dll
    pthreads  
       lib
       dll
    flint
       lib
       dll
    arb
       build.vc
       lib
       dll

 
Here the lib and dll sub-directories for each application hold the 
static and dynamic link library outputs which will be used when 
ARB is built. They each contain up to four sub-directories for 
the normal configurations for building on Windows:

    Win32\Release

    Win32\Debug

    x64\Release

    x64\Debug

To build ARB for a particular configuration requires that each
of the four libraries on which ARB depends must have been 
previously built for the same configuration.

Opening the solution file arb\build.vc\arb.sln provides the 
following build projects:

arb_config - a Python program for creating the Visual Studio 
               build files

build_tests -  a Python program for building the ARB tests 
               (after they have been created)

run_tests -   a Python program for running the ARB tests 
              (after they have been built)

The first step in building ARB is to generate the Visual 
Studio build files for the version of Visual Studio being used. 
This is done by running the Python application arb_config.py, 
either from within Visual Studio or on the command line. It is 
run with a single input parameter which is the last two digits 
of the Visual Studio version selected for building ARB (the 
default is 19 if no input is given).

Ths creates a build directory in the Flint root directory, for 
example:

    arb\build.vs19

that contains the file arb.sln which can now be loaded into 
Visual Studio and used to build the ARB library.
  
Once the ARB library has been built, the ARB tests can now 
be built and run by returning to the Visual Studio solution:

    arb\build.vc\arb.sln

and running the build_tests and run_tests Python applications.

After building ARB, the libraries and the header files that
you need to use ARB are placed in these directories in the 
ARB root directory:

lib\<Win32|x64>\<Debug|Release>

dll\<Win32|x64>\<Debug|Release>

depending on the version(s) that have been built.
   
      Brian Gladman
      24th June 2020

