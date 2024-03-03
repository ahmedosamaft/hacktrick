import requests
import numpy as np
from LSBSteg import encode
from riddle_solvers import *

api_base_url = "http://3.70.97.142:5000"
team_id = "kNgGFJe"
msg=""
current_fake = 0 

test_case = get_riddle(team_id,"problem_solving_easy")
sol = solve_problem_solving_easy(test_case)
if solve_riddle(team_id,sol): current_fake += 1