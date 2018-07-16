"""
Changelog:
    v1.0 - Created. <08/03/2017>

Author: Arthur Zachow Coelho (arthur.zachow@gmail.com)
Created: 08/03/2017

This module has the classes used in the simulation.
"""
from time import localtime
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

    >>> type(Driver(OD(1, 2, 8, 15)))
    <class '__main__.Driver'>
    '''

    def __init__(self, OD):
        """
        Class constructor.

        >>> isinstance(Driver(OD(1, 2, 8, 15)), Driver)
        True
        >>> isinstance(Driver(1), Driver)
        True
        >>> isinstance(Driver(OD(1, 2, 8, 15)).od, OD)
        True

        The class contructor needs to be more precise about its input.
        """
        self.od = OD

    def od_s(self):
        """
        String of OD pair of the Driver.
        Could be substituted by the __repr__ method.

        >>> Driver(1).od_s()
        Traceback (most recent call last):
        ...
        AttributeError: 'int' object has no attribute 'o'
        >>> Driver(OD(1, 2, 8, 15)).od_s()
        '12'
        """
        return "%s%s" % (self.od.o, self.od.d)

    def __repr__(self):
        """
        __repr__ method override.

        >>> Driver(OD(1, 2, 8, 15))
        '1|2'
        """
        return repr(str(self.od.o) + '|' + str(self.od.d))


class OD(object):
    """
    Represents an origin-destination pair, where:

    Inputs:
    origin: string = origin node
    destiny: string = destination node
    num_path: int = number of shortest paths to generate
    num_travels: int = number of travels

    Tests to verify the attributes:
    >>> isinstance(OD('A', 'B', 5, 100), OD)
    True
    >>> type(OD('A', 'B', 5, 100))
    <class '__main__.OD'>
    >>> isinstance(OD(1, 2, 3, 4).o, int)
    True
    >>> isinstance(OD('A', 'B', 5, 100).o, str)
    True

    Tests #3 and #4 sugests that self.o and self.d need to be more strictly
    controlled perhaps converting the O and the D to a string is a solution.

    ** OD notation: origin|destiny
    """

    def __init__(self, origin, destiny, num_paths, num_travels):
        """
        Class Constructor.

        >>> OD('A', 'B', 5, 100).o
        'A'
        >>> OD('A', 'B', 5, 100).d
        'B'
        >>> OD('A', 'B', 5, 100).numPaths
        5
        >>> OD('A', 'B', 5, 100).numTravels
        100
        >>> OD('A', 'B', 5, 100).paths
        """
        self.o = origin
        self.d = destiny
        self.numPaths = num_paths
        self.numTravels = num_travels
        self.paths = None

    def __str__(self):
        """
        __str__ method override.

        >>> print OD('A', 'B', 5, 100)
        Origin: A, Destination: B, Number of travels: 100, Number of shortest paths: 5
        """
        return "Origin: " + str(self.o) + ", Destination: " + str(self.d) + \
            ", Number of travels: " + str(self.numTravels) + ", Number of shortest paths: " \
            + str(self.numPaths)


class Output(object):
    def __init__(self, infos):
        #Dictionary with the experiment information
        self.infos = infos

    def build_od_pair_data(self, ttByOD):
        """
        Returns the string of OD pair data for each OD.
        Not tested yet, need to test QL module first.
        """
        str_od = ''
        for k in ttByOD.keys():
            if len(ttByOD[k]) == 0:
                str_od = '0'
            else:
                str_od += " %4.4f" % (sum(ttByOD[k]) / len(ttByOD[k]))

        return str_od + ' '

    def create_header(self):
        headerstr = "#Parameters:" + "\n#\tAlpha=" + str(self.infos["alpha"])

        if self.infos["action_selection"] == "epsilon":
            headerstr += "\tEpsilon=" + str(self.infos["epsilon"])

        elif self.infos["action_selection"] == "boltzmann":
            headerstr += "\tTemperature=" + str(self.infos["temperature"])

        headerstr += "\n#\tDecay=" + str(self.infos["decay"]) + "\tNumber of drivers="
        headerstr += str(self.infos["num_drivers"]) + "\n#\tGroup size="
        headerstr += str(self.infos["group_size"]) + "\tQL Table init="
        headerstr += str(self.infos["TABLE_INITIAL_STATE"]) +  "\n#\tk=" + str(self.infos["num_routes"])

        if self.infos["TABLE_INITIAL_STATE"] == "fixed":
            headerstr += "\t\tFixed value=" + str(self.fixed)
        elif self.infos["TABLE_INITIAL_STATE"] == "random":
            headerstr += "\t\tMax=" + str(self.maxi) + "\n#\tMin=" + str(self.mini)

        headerstr += "\n#Episode AVG_TT " + utils.nodes_string(self.printODpair, self.printTravelTime,
                                                         self.printDriversPerLink,
                                                         self.printDriversPerRoute, self.ODlist,
                                                         self.edgeNames, self.ODheader)
        return headerstr

    def createStringArguments(self):
        if useQL: #Experiment type 3
            fmt = "./results_gaql_grouped/net_%s/QLGA/pm%4.4f/crossover_%.2f/decay%4.3f/alpha%3.2f"
            path = fmt % (self.network_name, self.mutation, self.crossover, self.decay, self.alpha)

            filename += '_a' + str(self.alpha) + '_d' + str(self.decay)
            headerstr += "\n#\tAlpha=" + str(self.alpha) + "\tDecay=" + str(self.decay) \

            if self.action_selection == "epsilon":
                headerstr += "\n#\tEpsilon=" + str(self.epsilon)
            elif self.action_selection == "boltzmann":
                headerstr += "\n#\tTemperature=" + str(self.temperature)

            headerstr += "\tQL table init=" + str(self.TABLE_INITIAL_STATE)

            if self.TABLE_INITIAL_STATE == "fixed":
                headerstr += "\n#\tFixed value=" + str(self.fixed)
            elif self.TABLE_INITIAL_STATE == "random":
                headerstr += "\n#\tMax=" + str(self.maxi) + "\t\tMin=" + str(self.mini)


            headerstr_ext += " QL_AVG_TT"

            if useInt: #Experiment type 4
                fmt = "./results_gaql_grouped/net_%s/GAQL/" \
                       + "pm%4.4f/crossover_%.2f/decay%4.3f/alpha%3.2f"

                path = fmt % (self.network_name, self.mutation, self.crossover, self.decay, self.alpha)
                filename += '_interval'+ str(self.interval)
                headerstr += "\n#\tGA<->QL interval=" + str(self.interval)

        headerstr += headerstr_ext + utils.nodes_string(self.printODpair, self.printTravelTime,
                                                  self.printDriversPerLink, self.printDriversPerRoute,
                                                  self.ODlist, self.edgeNames, self.ODheader)

        return filename, path, headerstr


class QlOutput(Output):
    def __init__(self, infos):
        super.__init__(infos)
        self.path = self.create_path()
        self.filename = self.create_filename()
        #Creates folder to create the file
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

        self.output_file = open(self.filename, 'w')
        self.output_file.write(self.create_header() + '\n')

    def __print_step(self, step_number, stepSolution, output_file, avgTT=None, qlTT=None):
        """
        Write infos to the output file.
            step_number:int = episode/generation
            step_solution:QL = instance of QL class.
        """

        if step_number % self.printInterval == 0:
            if self.useGA:
                if self.useQL:
                    output_file.write(str(step_number) + " " + str(avgTT) +" "+ str(qlTT))
                else:
                    output_file.write(str(step_number) + " " + str(avgTT) + " ")
            else:
                output_file.write(str(step_number) + " " + str(qlTT)+" ")

            if self.printODpair:
                ttByOD = self.travelTimeByOD(stepSolution)
                output_file.write(self.build_od_pair_data(ttByOD))

            if self.printTravelTime:
                travel_times = ''
                edges = self.calculate_edges_travel_times(stepSolution)
                for edge in self.edgeNames:
                    travel_times += str(edges[edge]) + " "
                output_file.write(travel_times.strip() + " ")

            if self.printDriversPerLink:
                drivers = ''
                edges = self.driversPerLink(stepSolution)
                for edge in self.edgeNames:
                    drivers += str(edges[edge]) + " "
                output_file.write(drivers.strip())

            if self.printDriversPerRoute:
                self.TABLE_FILL = utils.clean_od_table(self.ODL, self.k)
                for s in range(len(stepSolution)):
                    self.TABLE_FILL[str(self.drivers[s].od.o)
                                    + str(self.drivers[s].od.d)][stepSolution[s]] += 1
                .write(" ")
                for keys in self.ODL:  # Now it prints in the correct order
                    for x in range(len(self.TABLE_FILL[keys])):
                        output_file.write(str(self.TABLE_FILL[keys][x]) + " ")

            output_file.write("\n")

    def create_path(self):
        """
            Creates the output file path.
        """
        fmt = "./results_gaql_grouped/net_%s/QL/decay%4.3f/alpha%3.2f"
        path = fmt % (self.network_name, self.infos["decay"], self.infos["alpha"])

        return path

    def create_filename(self):
        """
            Creates the output file name.
        """
        path = self.create_path()
        filename = path + '/' + self.network_name + '_k' + str(self.infos["num_routes"]) + '_a'
        filename += str(self.infos["alpha"]) + '_d' + str(self.infos["decay"]) + '_' + str(localtime()[3])
        filename += 'h' + str(localtime()[4]) + 'm' + str(localtime()[5]) + 's'
        filename = utils.appendTag(filename)

        return filename

    def create_header(self):
        headerstr = "#Parameters:" + "\n#\tAlpha=" + str(self.infos["alpha"])

        if self.infos["action_selection"] == "epsilon":
            headerstr += "\tEpsilon=" + str(self.infos["epsilon"])

        elif self.infos["action_selection"] == "boltzmann":
            headerstr += "\tTemperature=" + str(self.infos["temperature"])

        headerstr += "\n#\tDecay=" + str(self.infos["decay"]) + "\tNumber of drivers="
        headerstr += str(self.infos["num_drivers"]) + "\n#\tGroup size="
        headerstr += str(self.infos["group_size"]) + "\tQL Table init="
        headerstr += str(self.infos["TABLE_INITIAL_STATE"]) +  "\n#\tk=" + str(self.infos["num_routes"])

        if self.infos["TABLE_INITIAL_STATE"] == "fixed":
            headerstr += "\t\tFixed value=" + str(self.fixed)
        elif self.infos["TABLE_INITIAL_STATE"] == "random":
            headerstr += "\t\tMax=" + str(self.maxi) + "\n#\tMin=" + str(self.mini)

        headerstr += "\n#Episode AVG_TT " + utils.nodes_string(self.printODpair, self.printTravelTime,
                                                         self.printDriversPerLink,
                                                         self.printDriversPerRoute, self.ODlist,
                                                         self.edgeNames, self.ODheader)
        return headerstr


class GaOutput(Output):
    def __init__(self, infos):
        super.__init__(infos)
        self.path = self.create_path()
        self.filename = self.create_filename()
        #Creates folder to create the file
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

        self.output_file = open(self.filename, 'w')
        self.output_file.write(self.create_header() + '\n')

    def __print_step(self, step_number, stepSolution, output_file, avgTT=None, qlTT=None):
        """
        Write infos to the output file.
            step_number:int = episode/generation
            step_solution:QL = instance of QL class.
        """

        if step_number % self.printInterval == 0:
            if self.useGA:
                if self.useQL:
                    output_file.write(str(step_number) + " " + str(avgTT) +" "+ str(qlTT))
                else:
                    output_file.write(str(step_number) + " " + str(avgTT) + " ")
            else:
                output_file.write(str(step_number) + " " + str(qlTT)+" ")

            if self.printODpair:
                ttByOD = self.travelTimeByOD(stepSolution)
                output_file.write(self.build_od_pair_data(ttByOD))

            if self.printTravelTime:
                travel_times = ''
                edges = self.calculate_edges_travel_times(stepSolution)
                for edge in self.edgeNames:
                    travel_times += str(edges[edge]) + " "
                output_file.write(travel_times.strip() + " ")

            if self.printDriversPerLink:
                drivers = ''
                edges = self.driversPerLink(stepSolution)
                for edge in self.edgeNames:
                    drivers += str(edges[edge]) + " "
                output_file.write(drivers.strip())

            if self.printDriversPerRoute:
                self.TABLE_FILL = utils.clean_od_table(self.ODL, self.k)
                for s in range(len(stepSolution)):
                    self.TABLE_FILL[str(self.drivers[s].od.o)
                                    + str(self.drivers[s].od.d)][stepSolution[s]] += 1
                .write(" ")
                for keys in self.ODL:  # Now it prints in the correct order
                    for x in range(len(self.TABLE_FILL[keys])):
                        output_file.write(str(self.TABLE_FILL[keys][x]) + " ")

            output_file.write("\n")

    def create_path(self):
        """
            Creates the output file path.
        """
        fmt = "./results_gaql_grouped/net_%s/GA/pm%4.4f/crossover_%.2f"
        path = fmt % (self.infos["network_name"], self.infos["mutation"], self.infos["crossover"])

        return path

    def create_filename(self):
        """
            Creates the output file name.
        """
        path = self.create_path()
        filename = path + '/net' + self.network_name + '_pm' + str(self.infos["mutation"]) + '_c'
                 + str(self.infos["crossover"]) + '_e' + str(self.infos["elite"]) + '_k' + str(self.infos["num_routes")
        filename += '_d' + str(self.decay) + '_' + str(localtime()[3]) + 'h' + str(localtime()[4]) + 'm' + str(localtime()[5]) + 's'
        filename = utils.appendTag(filename)

        return filename

    def create_header(self):
        headerstr = "#Parameters:" + "\n#\tGenerations=" + str(self.generations) + "\tPopulation=" \
                  + str(self.population) + "\n#\tMutation=" + str(self.mutation) + "\tCrossover=" \
                  + str(self.crossover) + "\n#\tElite=" + str(self.elite) + "\t\tGroup size=" \
                  + str(self.group_size) + "\n#\tk=" + str(self.k) + "\t\tNumber of drivers=" \
                  + str(utils.nd(self.drivers, self.group_size))

        headerstr += "\n#Generation AVG_TT " + utils.nodes_string(self.printODpair, self.printTravelTime,
                                                         self.printDriversPerLink,
                                                         self.printDriversPerRoute, self.ODlist,
                                                         self.edgeNames, self.ODheader)
        return headerstr

