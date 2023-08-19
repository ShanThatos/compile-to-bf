from .units import *

UNIT = Workspace([unit])
SHIFTER = Workspace([shifter1, shifter2])
COMPUTE = Workspace([query_data, compute_extra, query, compute, ins_router], compute.running)
REGISTER = Workspace([register])
