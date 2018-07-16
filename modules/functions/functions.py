# -*- coding: utf-8 -*-

"""
Changelog:
    V1.0 - Created. <08/03/2017>

Author: Arthur Zachow Coelho (arthur.zachow@gmail.com)
Created: 08/03/2017

This module contains the functions used in the simulation.
"""
#Python native modules
import string
import os
import sys
#Third-party modules
from py_expression_eval import Parser
#Own modules
import modules.experiment.classes as Classes
import ksp.KSP as KSP

def is_number(arg):
    '''
    This function try to convert whatever is its argument to a float number.

    Input:
        arg:Anything = The object that it tries to convert to a number.
    Output:
        True if it converts successfully to a float.
        False if it can't, by getting a ValueError exception.

    >>> is_number(1)
    True
    >>> is_number(1e1000)
    True
    >>> is_number('5000')
    True
    >>> is_number(3.141598)
    True
    >>> is_number('a')
    False
    >>> is_number('hello')
    False
    >>> is_number(Node('a'))
    Traceback (most recent call last):
    ...
    TypeError: float() argument must be a string or a number
    '''
    try:
        float(arg)
        return True
    except ValueError:
        return False

def generate_table_fill(coupling_file):
    """
    Read the coupling file contents and create the table fill.

    In:
        coupling_file:String = Path to coupling file.
    Out:
        table_fill:Dictionary = Table fill.
    """
    table_fill = {}
    for line in open(coupling_file, 'r'):
        if line.strip() != '':
            line = line.split()
            if '#' not in line[0]:
                list_values = []
                for value in line:
                    if value != line[0]:
                        list_values.append(float(value))
                table_fill[line[0]] = list_values

    return table_fill

def clean_od_table(od_list, k):
    """
    Zeroes the OD table.
    In:
        od_list:OD = List of the OD pairs.
        k:Integer = Desired K at which it found the best routes.
    Out:
        table_fill:Dictionary = Q-table fill.
    """
    table_fill = {}
    for od_pair in od_list:
        table_fill[str(od_pair)] = [0] * k

    return table_fill

def read_infos(graph_file, flow):
    """
    Read the edges and OD pairs from the file in this program format(with the functions of each).
    In:
        graph_file:String = Path to the network file.
        flow:Integer = Base flow of the network.
    Out:
        vo:Node = List of the nodes of the network.
        new_edges:EdgeRC = List of edges in the correct form for this program.
        od_list:OD = List of OD pairs of the network.
    """
    functions = {}
    new_edges = []
    od_list = []

    #Uses the KSP function to get the infos
    vertices, edges, _ = KSP.generateGraph(graph_file, flow=flow)

    #Read again the file to store information in the correct form
    for line in open(graph_file, 'r'):
        taglist = string.split(line)
        if taglist[0] == 'function':
            variables = []
            variables = taglist[2].replace('(', '')
            variables = variables.replace(')', '')
            variables = variables.split(',')
            functions[taglist[1]] = [taglist[3], variables]

        elif taglist[0] == 'dedge' or taglist[0] == 'edge':
            constants = []
            cost_formula = ""
            freeflow_cost = 0
            constant_acc = 0
            if len(taglist) > 5:
                i = 5
                while i <= (len(taglist) - 1):
                    constants.append(taglist[i])
                    i += 1
                parser = Parser()
                ##[4] is function name.[0] is expression
                exp = parser.parse(functions[taglist[4]][0])
                LV = exp.variables()
                buffer_LV = []
                for l in LV:
                    if l not in functions[taglist[4]][1]:
                        constant_acc += 1
                        buffer_LV.append(l)

                #check if the formula has any parameters(variables)
                flag = False
                for v in functions[taglist[4]][1]:
                    if v in LV:
                        flag = True

                buffer_dic = {}
                i = 0
                for index in range(constant_acc):
                    buffer_dic[buffer_LV[index]] = float(constants[index])
                    i = 1

                if not flag:
                    freeflow_cost = exp.evaluate(buffer_dic)
                    cost_formula = str(freeflow_cost)

                elif is_number(functions[taglist[4]][0]):
                    cost_fomula = functions[taglist[4]][0]

                else:
                    exp = exp.simplify(buffer_dic)
                    cost_formula = exp.toString()

                for edge in edges:
                    if edge.name == taglist[1] and (edge.start == taglist[2] \
                        or edge.start == taglist[3]) and (edge.end == taglist[2] \
                        or edge.end == taglist[3]):
                        new_edges.append(Classes.EdgeRC(edge.name, edge.start, edge.end, edge.cost,
                                                        cost_formula))
                        if taglist[0] == 'edge':
                            new_edges.append(Classes.EdgeRC('%s-%s'%(edge.end, edge.start), edge.end,
                                                            edge.start, edge.cost, cost_formula))

            else:
                cost_formula = ""
                freeflow_cost = 0
                parser = Parser()
                if is_number(functions[taglist[4]][0]):
                    cost_formula = functions[taglist[4]][0]

                else:
                    exp = parser.parse(functions[taglist[4]][0])
                    cost_formula = exp.toString()

                for edge in edges:
                    if edge.name == taglist[1] and (edge.start == taglist[2] or edge.start == taglist[3]) \
                    and (edge.end == taglist[2] or edge.end == taglist[3]):
                        new_edges.append(Classes.EdgeRC(edge.name, edge.start, edge.end, edge.cost,
                                                        cost_formula))
                        if taglist[0] == 'edge':
                            new_edges.append(Classes.EdgeRC(edge.name, edge.end, edge.start, edge.cost,
                                                            cost_formula))

        elif taglist[0] == 'od':
            od_list.append((taglist[2], taglist[3], float(taglist[4])))

    return  vertices, new_edges, od_list

# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Got from: https://gist.github.com/aubricus/f91fb55dc6ba5557fbab06119420dd6a

    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()
