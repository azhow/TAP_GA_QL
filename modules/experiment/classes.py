"""
Changelog:
    v1.0 - Created. <08/03/2017>

Author: Arthur Zachow Coelho (arthur.zachow@gmail.com)
Created: 08/03/2017

This module has the classes used in the simulation.
"""
from py_expression_eval import Parser
from ksp.KSP import Edge


class EdgeRC(Edge):
    """
    Represents an edge for the route_choice program.
    Inherits from the Edge class from the KSP code.
    In:
        function:String = The cost function.
    """
    def __init__(self, name, start, end, cost, function):
        Edge.__init__(self, name, start, end, cost)
        self.function = function

    def __repr__(self):
        return repr(self.name)

    def eval_cost(self, var_value):
        """
        Calculates the value of the cost formula at a given value.
        In:
            var_value:Float = Variable value.

        Out:
            value:Float = result of the calculation.
        """
        parser = Parser()
        expression = parser.parse(self.function)
        return expression.evaluate({'f':var_value})


class Driver(object):
    '''
    Represents a driver in the network.

    Input:
    od: OD = instance of OD class
    '''

    def __init__(self, origin_destination):
        """
        Class constructor.
        """
        self.origin_destination = origin_destination

    def od_s(self):
        """
        String of OD pair of the Driver.
        """
        return "%s%s" % (self.origin_destination.origin, self.origin_destination.destination)

    def __str__(self):
        return "%s%s" % (self.origin_destination.origin, self.origin_destination.destination)

    def __repr__(self):
        """
        __repr__ method override.
        """
        return repr(str(self.origin_destination.origin) + '|' +
                    str(self.origin_destination.destination))


class OriginDestination(object):
    """
    Represents an origin-destination pair, where:

    Inputs:
    origin: string = origin node
    destiny: string = destination node
    num_path: int = number of shortest paths to generate
    num_travels: int = number of travels

    Tests to verify the attributes:
    ** OD notation: origin|destiny
    """

    def __init__(self, origin, destiny, num_paths, num_travels):
        """
        Class Constructor.
        """
        self.origin = origin
        self.destination = destiny
        self.num_paths = num_paths
        self.num_travels = num_travels
        self.paths = None

    def __str__(self):
        """
        __str__ method override.
        """
        return "Origin: " + str(self.origin) + ", Destination: " + str(self.destination) + \
            ", Number of travels: " + str(self.num_travels) + ", Number of shortest paths: " \
            + str(self.num_paths)
