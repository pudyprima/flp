# -*- coding: utf-8 -*-
"""
Created on Wed Dec 06 13:47:38 2017

@author: Pudy Prima
"""
import sys
import time
import random
from pulp import splitDict, makeDict, LpVariable, LpProblem, lpSum, LpInteger, LpMinimize, value

SD_DATASET1 = "data/dummy_sd"
SD_DATASET2 = "data/cap63_sd"
SD_DATASET3 = "data/capc4_sd"

def sdflp_greedy(facilities, clients, demands):
    """
    Finding optimal solution of single-demand facility location problem
    using greedy approach.
    """
    demand = demands.values()[0]

    start_time = time.time()
    opt_facilities = []
    opt_assignments = []

    # Sort and reindex facilities
    f_sorted = sorted(facilities, key=lambda f: (f[0]+f[1]*f[2])/f[2])

    # Determine small and big facilities
    bigs = []
    small_sum = 0
    status = 's'

    for facility in f_sorted:
        if small_sum + facility[2] < demand:
            # Small facility
            if status == 'b':
                status = 's'

            opt_facilities.append(facility)
            opt_assignments.append(facility[2])
            small_sum += facility[2]
        else:
            # Big facility
            if status == 's':
                status = 'b'
                bigs = []

            bigs.append(facility)

    # Determine big facility with minimum cost
    min_cost = sys.maxint
    min_big = None
    remainder = demand - small_sum
    for big in bigs:
        cost = big[0] + big[1] * remainder
        if cost < min_cost:
            min_cost = cost
            min_big = big

    opt_facilities.append(min_big)
    opt_assignments.append(remainder)
    exec_time = time.time() - start_time
    
    for i in range(len(opt_facilities)):
        print "{} - {} = {}".format(opt_facilities[i][3], clients[0], opt_assignments[i])
    print "Total cost - Total demand = ", calculate_cost_demand(opt_facilities, opt_assignments)
    print "Execution time = ", exec_time
    return exec_time

def sdflp_greedy_fractional(facilities, clients, capacity_fixedcost, demands, costs):
    """
    Finding optimal solution of single-demand facility location problem
    using greedy approach.
    """

    start_time = time.time()
    opt_facilities = []
    opt_assignments = []
    small_sum = 0
    remainder = demands.values()[0]

    # Sort and reindex facilities
    f_sorted = sorted(facilities, key=lambda f: (f[0]+f[1]*f[2])/f[2])

    for f in f_sorted:
        if small_sum + f[2] < remainder:
            opt_facilities.append(f)
            opt_assignments.append(f[2])
            remainder -= f[2]
        else:
            opt_facilities.append(f)
            opt_assignments.append(remainder)
            break
    exec_time = time.time() - start_time
    
    for i in range(len(opt_facilities)):
        print "{} - {} = {}".format(opt_facilities[i][3], clients[0], opt_assignments[i])
    print "Total cost - Total demand = ", calculate_cost_demand(opt_facilities, opt_assignments)
    print "Execution time = ", exec_time
    return exec_time

def flp_linprog(facilities, clients, capacity_fixedcost, demands, costs):
    start_time = time.time()

    # Creates a list of tuples containing all the possible routes for transport
    Routes = [(f,l) for f in facilities for l in clients]

    # Splits the dictionaries to be more understandable
    (capacities, fixedcosts) = splitDict(capacity_fixedcost)

    # The cost data is made into a dictionary
    costs = makeDict([facilities, clients], costs, 0)

    # Creates the problem variables of the Flow on the Arcs
    flow = LpVariable.dicts("Route", (facilities, clients), 0, None, LpInteger)

    # Creates the master problem variables of whether to build the Plants or not
    build = LpVariable.dicts("BuildaFacility", facilities, 0, 1, LpInteger)

    # Creates the 'prob' variable to contain the problem data
    prob = LpProblem("Facility Location Problem", LpMinimize)

    # The objective function is added to prob - The sum of the transportation costs and the building fixed costs
    prob += lpSum([flow[f][l] * costs[f][l] for (f,l) in Routes]) + lpSum([fixedcosts[f] * build[f] for f in facilities]),"Total Costs"

    # The Supply maximum constraints are added for each supply node (plant)
    for f in facilities:
        prob += lpSum([flow[f][l] for l in clients]) <= capacities[f] * build[f], "Sum of Products out of Plant %s"%f

    # The Demand minimum constraints are added for each demand node (store)
    for l in clients:
        prob += lpSum([flow[f][l] for f in facilities]) >= demands[l], "Sum of Products into Stores %s"%l

    prob.solve()
    exec_time = time.time() - start_time

    for v in prob.variables():
        if "BuildaPlant" in v.name:
            if v.varValue == 1:
                print(v.name, "=", v.varValue)
        if "Route" in v.name:
            if v.varValue > 0:
                print(v.name, "=", v.varValue)
    
    # The optimised objective function value is printed to the screen    
    print "Total Costs = ", value(prob.objective)
    print "Execution time = ", exec_time
    return exec_time

def parser(dataset):
    datafile = open(dataset)
    lines = datafile.readlines()

    content = map(int, lines[0].split())
    num_facilities, num_clients = content[0], content[1]
    facilities = ["F{}".format(i) for i in range(num_facilities)]
    clients = ["L{}".format(i) for i in range(num_clients)]

    capacity_fixedcost_list = []
    for i in range(1, num_facilities + 1):
        content = capacity_fixedcost_list.append(map(float, lines[i].split()))
    capacity_fixedcost = dict(zip(facilities, capacity_fixedcost_list))

    content = map(float, lines[num_facilities + 1].split())
    demands = dict(zip(clients, content))

    costs = []
    for i in range(num_facilities + 2, 2 * num_facilities + 2):
        costs.append(map(float, lines[i].split()))

    return facilities, clients, capacity_fixedcost, demands, costs

def generate_random(num_facilities, num_clients):

    facilities = ["F{}".format(i) for i in range(num_facilities)]
    clients = ["L{}".format(i) for i in range(num_clients)]
    
    generate_capacities = random.sample(range(1, 100000), num_facilities)
    generate_fixedcosts = random.sample(range(0, 100000), num_facilities)
    capacity_fixedcost = dict(zip(facilities, zip(generate_capacities, generate_fixedcosts)))
    
    generate_demands = random.sample(range(100, 100000), num_clients)
    demands = dict(zip(clients, generate_demands))
    
    costs = []
    for i in range(num_facilities):
        costs.append(random.sample(range(0, 10000), num_clients))
    
    return facilities, clients, capacity_fixedcost, demands, costs

def calculate_cost_demand(list_facilities, list_assignments):
    total_cost = 0
    total_demand = 0

    for i in range(len(list_facilities)):
        total_cost += list_facilities[i][0] + list_facilities[i][1]*list_assignments[i]
        total_demand += list_assignments[i]

    return total_cost, total_demand

def convert_to_greedy_form(facilities, capacity_fixedcost, costs):
    greedy_facilities = []
    
    for i in range(len(facilities)):
        temp_f = []
        temp_f.append(capacity_fixedcost.values()[i][1])
        temp_f.append(costs[i][0])
        temp_f.append(capacity_fixedcost.values()[i][0])
        temp_f.append(capacity_fixedcost.keys()[i])
        greedy_facilities.append(temp_f)
    
    return greedy_facilities

def test_running_time(num_iter, num_facilities, num_clients):
    greedy_total_running_time = 0
    greedyfractional_total_running_time = 0
    linprog_total_running_time = 0

    for i in range(num_iter):
        print i
        # 1.1 DATA SET SD
        facilities, clients, capacity_fixedcost, demands, costs = generate_random(num_facilities, num_clients)
        greedy_facilities = convert_to_greedy_form(facilities, capacity_fixedcost, costs)
    
        # 1.1.1 GREEDY
        greedy_total_running_time += sdflp_greedy(greedy_facilities, clients, demands)
    
        # 1.1.2 GREEDY_FRACTIONAL
        greedyfractional_total_running_time += sdflp_greedy_fractional(greedy_facilities, clients, capacity_fixedcost, demands, costs)
    
        # 1.1.3 LINEAR_PROGRAMMING
        linprog_total_running_time += flp_linprog(facilities, clients, capacity_fixedcost, demands, costs)

    return (float)(greedy_total_running_time/num_iter), (float)(greedyfractional_total_running_time/num_iter), (float)(linprog_total_running_time/num_iter)

def main():
    # EXPERIMENTS

    # 1. Experiment - SINGLE DEMAND

    # Random dataset
    facilities, clients, capacity_fixedcost, demands, costs = generate_random(500, 1)
    greedy_facilities = convert_to_greedy_form(facilities, capacity_fixedcost, costs)

    # GREEDY
    sdflp_greedy(greedy_facilities, clients, demands)

    # GREEDY_FRACTIONAL
    sdflp_greedy_fractional(greedy_facilities, clients, capacity_fixedcost, demands, costs)

    # LINEAR_PROGRAMMING
    flp_linprog(facilities, clients, capacity_fixedcost, demands, costs)

#    # 1.1 DATA SET SD 1
#    facilities, clients, capacity_fixedcost, demands, costs = parser(SD_DATASET1)
#    greedy_facilities = convert_to_greedy_form(facilities, capacity_fixedcost, costs)
#
#    # 1.1.1 GREEDY
#    sdflp_greedy(greedy_facilities, clients, demands)
#
#    # 1.1.2 GREEDY_FRACTIONAL
#    sdflp_greedy_fractional(greedy_facilities, clients, capacity_fixedcost, demands, costs)
#
#    # 1.1.3 LINEAR_PROGRAMMING
#    flp_linprog(facilities, clients, capacity_fixedcost, demands, costs)

#    # 1.2 DATA SET SD 2
#    facilities, clients, capacity_fixedcost, demands, costs = parser(SD_DATASET2)
#    greedy_facilities = convert_to_greedy_form(facilities, capacity_fixedcost, costs)
#
#    # 1.2.1 GREEDY
#    sdflp_greedy(greedy_facilities, clients, demands)
#
#    # 1.2.2 GREEDY_FRACTIONAL
#    sdflp_greedy_fractional(greedy_facilities, clients, capacity_fixedcost, demands, costs)
#
#    # 1.2.3 LINEAR_PROGRAMMING
#    flp_linprog(facilities, clients, capacity_fixedcost, demands, costs)
#
#    # 1.3 DATA SET SD 3
#    facilities, clients, capacity_fixedcost, demands, costs = parser(SD_DATASET3)
#    greedy_facilities = convert_to_greedy_form(facilities, capacity_fixedcost, costs)
#
#    # 1.3.1 GREEDY
#    sdflp_greedy(greedy_facilities, clients, demands)
#
#    # 1.3.2 GREEDY_FRACTIONAL
#    sdflp_greedy_fractional(greedy_facilities, clients, capacity_fixedcost, demands, costs)
#
#    # 1.3.3 LINEAR_PROGRAMMING
#    flp_linprog(facilities, clients, capacity_fixedcost, demands, costs)
    
#    # 2. Running time experiment
#    print "(greedy, greedyfractional, linearprogramming) : ", test_running_time(100, 10000, 1)

    print "Exiting.."

if __name__ == "__main__":
    main()
