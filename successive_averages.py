#!/usr/bin/python3
'''
Created on 09/01/2015

@author: gabriel

New version by: Arthur Zachow Coelho (azcoelho@inf.ufrgs.br)
Date: 20/09/2017

Updated version by: João Vitor B. Labres (jvblabres@inf.ufrgs.br)
Date: 04/08/2020
'''

#Python third-party modules
import string
import argparse
import os
from time import localtime
from py_expression_eval import Parser

class Node(object):
    """
    Represents a node in the graph.
    """
    def __init__(self, name):
        """
        In:
            name:String = Name of the node.
        """
        self.name = name        # name of the node
        self.dist = 1000000     # distance to this node from start node
        self.prev = None        # previous node to this node
        self.flag = 0           # access flag

    def __repr__(self):
        return repr(self.name)


class Edge(object):
    '''
    Represents an edge in the graph.
    '''
    def __init__(self, start, end, function, param_values, variable):
        self.name = "%s-%s" % (start,end)

        self.start = start # Start node of the edge
        self.end = end # End node of the edge

        self.function = function # The function to be applied
        self.params = param_values # The constant values for the function
        self.var = variable # The variable of the equation

        self.flow = 0
        self.cost = 0
        self.aux_flow = 0

        self.update_cost() # Update for the initial cost

    def update_cost(self):
        '''
        Using the function and params attributes, it updates the cost of the edge.
        '''
        self.params[self.var] = self.flow
        self.cost = self.function[2].evaluate(self.params)

    def __repr__(self):
        return str(str(self.start) + '-' + str(self.end))


def generateGraph(graph_file, flow=0.0):
    """
    Adapted version from the KSP repository version 1.44.
    Original is available at: https://github.com/maslab-ufrgs/ksp/releases/tag/V1.44
    Generates the graph from a text file following the specifications(available @
        http://wiki.inf.ufrgs.br/network_files_specification).
    In:
        graph_file:String = Path to the network(graph) file.
        flow:Float = Value to sum the cost of the edges.

    Out:
        V:List = List of vertices or nodes of the graph.
        E:List = List of the edges of the graph.
        OD:List = List of the OD pairs in the network.
    """
    V = [] # vertices
    E = [] # edges
    F = {} # cost functions
    OD = {} # OD pairs

    lineid = 0
    for line in open(graph_file, 'r'):
        lineid += 1
        # ignore \n
        line = line.rstrip()
        # ignore comments
        hash_pos = line.find('#')
        if hash_pos > -1:
            line = line[:hash_pos]

        # split the line
        taglist = line.split()
        if len(taglist) == 0:
            continue

        if taglist[0] == 'function':
            # process the params
            params = taglist[2][1:-1].split(',')
            if len(params) > 1:
                raise Exception('Cost functions with more than one parameter are not yet'\
                                'acceptable! (parameters defined: %s)' % str(params)[1:-1])

            # process the function
            function = Parser().parse(taglist[3])

            # process the constants
            constants = function.variables()
            if params[0] in constants: # the parameter must be ignored
                constants.remove(params[0])

            # store the function
            F[taglist[1]] = [params[0], constants, function]

        elif taglist[0] == 'node':
            V.append(Node(taglist[1]))

        elif taglist[0] == 'dedge' or taglist[0] == 'edge': # dedge is a directed edge
            # process the cost
            function = F[taglist[4]] # get the corresponding function
            # associate constants and values specified in the line (in order of occurrence)
            param_values = dict(zip(function[1], map(float, taglist[5:])))

            param_values[function[0]] = flow # set the function's parameter with the flow value

            # create the edge(s)
            E.append(Edge(taglist[2], taglist[3], function, param_values, function[0]))
            if taglist[0] == 'edge':
                E.append(Edge(taglist[3], taglist[2], function, param_values, function[0]))

        elif taglist[0] == 'od':
            if taglist[2] != taglist[3]:
                OD[taglist[1]] = float(taglist[4])

        else:
            raise Exception('Network file does not comply with the specification!'\
                            '(line %d: "%s")' % (lineid, line))

    return V, E, OD

def resetGraph(N):
    '''
    Reset graph's variables to default.
    '''
    for node in N:
        node.dist = 1000000.0
        node.prev = None
        node.flag = 0

def pickSmallestNode(N):
    '''
    Returns the smallest node in N but not in S.
    '''
    minNode = None
    for node in N:
        if node.flag == 0:
            minNode = node
            break
    if minNode == None:
        return minNode
    for node in N:
        if node.flag == 0 and node.dist < minNode.dist:
            minNode = node
    return minNode

def pickEdgesList(u, E):
    '''
    Returns the edges list of node u.
    '''
    uv = []
    for edge in E:
        if edge.start == u.name:
            uv.append(edge)
    return uv

def dijkstra(N, E, origin, destination, ignoredEdges):
    '''
    Dijkstra's shortest path algorithm.
    '''

    #reset the graph (so as to discard information from previous runs)
    resetGraph(N)

    # set origin node distance to zero, and get destination node
    dest = None
    for node in N:
        if node.name == origin:
            node.dist = 0
        if node.name == destination:
            dest = node

    u = pickSmallestNode(N)
    while u != None:
        u.flag = 1
        uv = pickEdgesList(u, E)
        n = None
        for edge in uv:
            # avoid ignored edges
            if edge in ignoredEdges:
                continue

            # take the node n
            for node in N:
                if node.name == edge.end:
                    n = node
                    break
            if n.dist > u.dist + edge.cost:
                n.dist = u.dist + edge.cost
                n.prev = u

        u = pickSmallestNode(N)
        # stop when destination is reached
        if u == dest:
            break

    # generate the final path
    S = []
    u = dest
    while u.prev != None:
        S.insert(0,u)
        u = u.prev
    S.insert(0,u)

    return S

def printGraph(N, E):
    '''
    Print vertices and edges.
    '''
    print('vertices:')
    for node in N:
        previous = node.prev
        if previous == None:
            print(node.name, node.dist, previous)
        else:
            print(node.name, node.dist, previous.name)
    print('edges:')
    for edge in E:
        print(edge.start, edge.end, edge.cost)

def calcPathLength(P, N, E):
    '''
    Calculate path P's cost.
    '''
    if type(P[0]) is Edge:
        P = getPathAsNodes(P, N, E)
    length = 0
    prev = None
    for node in P:
        if prev != None:
            length += [edge for edge in E if edge.start == prev.name and edge.end == node.name][0].cost
        prev = node

    return length

def getPathAsEdges(P, E):
    '''
    Get the edges in the path.
    '''
    path = []
    prev = None
    for node in P:
        if prev != None:
            path.append([edge for edge in E if edge.start == prev.name and edge.end == node.name][0])
        prev = node

    return path

def getPathAsNodes(P, N, E):
    '''
    Get the nodes in a path.
    '''
    path = []
    path.append(node for node in N if P[0].start == N.node)
    for edge in P:
        path.append(node for node in N if edge.end == N.node)
    return path

def printPath(path, N, E):
    '''
    Print the path S.
    '''
    #S = N
    #if type(path[0]) is Edge:
    #    S = E
    strout = ''
    for e in path:
        if strout != '':
            strout += ' - '
        strout += e.name

    print("%g = %s" % (calcPathLength(path, N, E), strout))

def pathToStr(path, N, E):
    if type(path[0]) is Node:
        path = getPathAsEdges(path, E)

    strout = ""
    for e in path:
        if strout != '':
            strout += ' - '
        strout += e.name

    return strout

def run_MSA(its, N, E, OD_matrix, net_file_basename, output):
    '''
    This function actually runs the method of successive averages and print the results to a file.
    In:
        its:Integer = Number of iterations.
        N:List = List of Nodes (from the Node class).
        E:List = List of Edges (from the Edge class).
        OD_matrix:Dictionary = Dictionary of the OD pairs and their demands.
    Out:
        UE:Float = Represents the average total time of the network.
    '''
    # initial value for phi
    phi = 1.0

    '''
    A nested dictionary data structure to store, for each OD pair,
    its routes, and, for each route, its edges and flows
    an entry can be said a 4-uple: (OD, route string, route, flow).
    '''

    od_routes_flow = {od : {} for od in OD_matrix}

    # iterations
    for n in range(1, its+1):

        # update phi
        phi = 1.0 / n

        # clear auxiliary flow of all links
        for e in E:
            e.aux_flow = 0
            #e.flow = 0

        # calculate auxiliary flow based on a all-or-nothing assignment
        min_routes = {}
        for od in OD_matrix:
            [o, d] = od.split("|")


            # compute shortest route
            route = getPathAsEdges(dijkstra(N, E, o, d, []), E)
            route_str = pathToStr(route, N, E)

            # store min route of this od pair
            min_routes[od] = [route_str, route]

            # if the min route is not in the od routes' list, add it
            if route_str not in od_routes_flow[od]:
                od_routes_flow[od][route_str] = [route, 0]

        # calculate current flow of all links
        for od in OD_matrix:
            for route in od_routes_flow[od]:
                # route flow on previous iteration
                vna = od_routes_flow[od][route][1]

                # auxiliary route flow (0 if not the current best route)
                fa = 0
                if route == min_routes[od][0]:
                    fa = OD_matrix[od]

                # route flow of current iteration
                vna = max((1 - phi) * vna + phi * fa, 0)

                # update flows and costs
                od_routes_flow[od][route][1] = vna
                for e in od_routes_flow[od][route][0]:
                    e.aux_flow += vna
                    #e.flow += vna

        for e in E:
            e.flow = e.aux_flow
            e.update_cost()

    # print the final assignment
    UE = evaluate_assignment(OD_matrix, od_routes_flow, net_file_basename, its, E, output=output)

    return UE, od_routes_flow

def evaluate_assignment(OD_matrix, od_routes_flow, net_file_basename, its, edge_list, output=True):
    '''
    This function evaluates the assignment.
    In:
        OD_matrix:Dictionary = Dictionary with the od pair as key and demand as value.
        od_routes_flow: = . (?)
        net_file_basename:String = Name of the network.
        its:Integer = Number of iterations.
        output:Boolean = If the results are to be printed somewhere.
    Out:
        UE:Float = Average travel time of the network.
    '''

    if output:
        #The defined results folder.
        path = './results/'
        #The filename is the network name + the time of the day it was run.
        fn = net_file_basename + '_' + str(localtime()[3]) + 'h' + str(localtime()[4]) + 'm' \
           + str(localtime()[5]) + 's'

        #Verifies the existence of the folder.
        if os.path.isdir(path) is False:
            os.makedirs(path)

        fh = open(path+fn, 'w')
        #Header
        #print('#net_name: ' + net_file_basename + ' iterations: ' + str(its), file=fh)
        fh.write('#net_name: ' + net_file_basename + ' iterations: ' + str(its) + '\n')
        #print("#od\troute\tflow\ttravel time\tdeviations", file=fh)
        fh.write("#od\troute\tflow\ttravel time\tdeviations\n")

    sum_tt = 0.0
    sum_deviations = 0
    delta_top = 0.0
    delta_bottom = 0.0

    for od in od_routes_flow:
        aux = []
        min_cost = float('inf')
        #Calculate some information of each route
        for route in od_routes_flow[od]:
            #Calculate cost of the route
            cost = 0.0
            for e in od_routes_flow[od][route][0]:
                cost += e.cost
                sum_tt += e.cost * od_routes_flow[od][route][1]
            #To handle imprecise double representation
            cost = round(cost * 100) / 100
            #Store minimum route cost of current OD pair
            if cost < min_cost:
                min_cost = cost

            #Store the values in a temporary data structure to allow
            #The calculations of the "deviations from best" measure
            aux.append([od, route, od_routes_flow[od][route][1], cost])
        #Read the temporary data structure and print the results
        for e in aux:
            #Calculate the "deviations from best" measure
            deviations = 0
            if e[3] > min_cost:
                deviations = e[2]
                sum_deviations += deviations
            #Update the top part of delta equation
            delta_top += e[2] * (e[3] - min_cost)
            if output:
                fh.write("{}\t{:^60}\t{:^6.2f}\t{:^5.2f}\t{:.2f}\n".format(e[0], e[1], e[2], e[3], float(deviations)))

		#Update the bottom part of delta equation
        delta_bottom += OD_matrix[od]# * min_cost
    #Overall results
    UE = (sum_tt / sum([x for x in OD_matrix.values()]))
    if output:
        fh.write("Average travel time: {} min\n".format(UE))
        fh.write("Deviations: {}\n".format(int(sum_deviations)))
        fh.write("AEC: {:.10f}\n".format(delta_top / delta_bottom))

    fh.write("Name\t" + "Time\t" + "Flow\n")
    for edge in edge_list:
        fh.write("{:^5}\t{:.4f}\t{:.1f}\n".format(edge.name, edge.cost, edge.flow))

    fh.close()

    return UE

def run(iterations, net_file='', node_list=None, edge_list=None, od_matrix=None, output=True):
    """
    Precisely the function of running the program.
    Either pass a network file xor (node_list and edge_list and od_matrix).
    In:
        net_file:String = String representing the path to the network file.
        iterations:Integer = Number of iterations to be run.
        node_list:List = List of Node objects.
        edge_list:List = List of Edge objects.
        od_matrix:Dictionary = OD pairs and demands.
        output:Boolean = If the results are to be printed.
    Out:
        node_list:List = List of Node objects.
        edge_list:List = List of Edge objects.
        od_matrix:Dictionary = OD pairs and demands.
        UE:Float = Represents the average total time of the network.
    """
    if net_file:
        #Read graph from network file
        node_list, edge_list, od_matrix = generateGraph(net_file)
    if node_list and edge_list and od_matrix:
        #Run MSA
        UE, od_routes_flow = run_MSA(iterations, node_list, edge_list, od_matrix,
                     os.path.basename(net_file).split('.')[0], output)

    print("Name\t" + "Time\t", "Flow")
    for edge in edge_list:
        print("{}\t{:.4f}\t{:.1f}".format(edge.name, edge.cost, edge.flow))

    return node_list, edge_list, od_matrix, UE, od_routes_flow

def main():
    """
    Upper level function to call the other functions.
    """
    #Parser things for the parameters
    prs = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  description="""
                                  The method of successive averages.
                                  V2.1
                                  """)

    prs.add_argument("-f", dest="file", required=True, help="The network file.\n")
    prs.add_argument("-i", "--iterations", type=int, default=1000, help="Number of iterations.\n")
    args = prs.parse_args()

    #Calls the run to effectively do the experiment
    run(args.iterations, net_file=args.file)


if __name__ == '__main__':
    main()
