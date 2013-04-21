# Source this file from the directory in which it is installed or modify
# the pathes below for your system in order to properly setup your
# environment to run the Datacasting Server Tools

# © [2007]. California Institute of Technology.  ALL RIGHTS RESERVED.
# U.S. Government sponsorship acknowledged. Any commercial use must be
# negotiated with the Office of Technology Transfer at the California
# Institute of Technology.

# This software is subject to U. S. export control laws and regulations
# (22 C.F.R. 120-130 and 15 C.F.R. 730-774). To the extent that the
# software is subject to U.S. export control laws and regulations, the
# recipient has the responsibility to obtain export licenses or other
# export authority as may be required before exporting such information
# to foreign countries or providing access to foreign nationals.

set DATACASTING_ROOT=`pwd`

set PYRSS2GEN="${DATACASTING_ROOT}/tps/PyRSS2Gen"
set DATACASTING_TOOLS="${DATACASTING_ROOT}/server"

if ( ${?PYTHONPATH} == 0 ) then
  setenv PYTHONPATH ${DATACASTING_TOOLS}:${PYRSS2GEN}
else
  setenv PYTHONPATH ${DATACASTING_TOOLS}:${PYRSS2GEN}:${PYTHONPATH}
endif

if ( ${?pre_PATH} == 0) then
  setenv pre_PATH ${PATH}
else
  setenv PATH ${pre_PATH}
endif

setenv PATH ${DATACASTING_TOOLS}:${PATH}
