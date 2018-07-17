import os
from time import localtime
import modules.functions.functions as utils


class Output(object):
    def __init__(self, infos, network_name, print_interval, print_od_pair, print_travel_time,
                 print_drivers_link, print_drivers_route):
        # Dictionary with the experiment information
        self.infos = infos
        self.network_name = network_name
        # Printing options
        self.print_interval = print_interval
        self.print_od_pair = print_od_pair
        self.print_travel_time = print_travel_time
        self.print_drivers_link = print_drivers_link
        self.print_drivers_route = print_drivers_route
        # Empty filename
        self.filename = ""

    def build_od_pair_data(self, travel_times_od):
        """
        Returns the string of OD pair data for each OD.
        Not tested yet, need to test QL module first.
        """
        str_od = ''
        for k in travel_times_od.keys():
            if len(travel_times_od[k]) == 0:
                str_od = '0'
            else:
                str_od += " %4.4f".format(sum(travel_times_od[k]) / len(travel_times_od[k]))

        return str_od + ' '

    def append_tag(self):
        """
            Test if there isn't already a file with the desired name, sometimes
            the repetitions of the experiments are less than 1s apart.

        In:
            fn_wo_tag:String = Filename without the tag.
        Out:
            filenamewithtag:String = Filename with the tag.
        """
        time = localtime()
        self.filename += str(time[3]) + 'h' + str(time[4]) + 'm' + str(time[5]) + 's'
        append_number = ''
        while os.path.isfile(self.filename + append_number + ".txt"):
            if append_number == '':
                append_number = "-1"
            else:
                append_number = "-" + str(int(append_number[1:]) + 1)
        self.filename = self.filename + append_number + ".txt"

    def nodes_string(self):
        """
        String of edges of the graph that will be printed or stored in the file.

        Out:
            nodes_str:String = String with the values of the desired parameters.
        """
        nodes_str = ''
        if self.print_od_pair:
            for od_pair in self.infos["od_list"]:
                nodes_str += "tt_%s ".format(repr(od_pair))
        if self.print_travel_time:
            for edge in self.infos["edge_names"]:
                nodes_str += 'tt_' + edge + ' '
        if self.print_drivers_link:
            for edge in self.infos["edge_names"]:
                nodes_str += "nd_" + edge + ' '
        if self.print_drivers_route:
            nodes_str += self.infos["od_header"]  # Need to check what this really is
        nodes_str = nodes_str.strip()

        return nodes_str

    def get_number_drivers(self):
        """
        Number of drivers.
        """
        return len(self.infos["drivers"]) * self.infos["group_size"]

    def travel_time_od(self, string_actions):
        edgesTravelTimes = self.calculate_edges_travel_times(string_actions)
        od_travel_time_dict = {}

        for od in self.infos["ODlist"]:
            od_travel_time_dict["%s%s".format(od.origin, od.destination)] = []

        for driverIdx, action in enumerate(string_actions):
            path = self.drivers[driverIdx].od.paths[action][0]
            traveltime = 0.0
            for edge in path:
                traveltime += edgesTravelTimes[edge]
            od_travel_time_dict[str(self.drivers[driverIdx].origin_destination)].append(traveltime)

        return od_travel_time_dict

    def calculate_edges_travel_times(self, string_actions):
        edges_travel_times = {}
        # Get the flow of that edge
        link_occupancy = self.driversPerLink(string_actions)
        # For each edge
        for edge in self.Eo:
            # Evaluates the cost of that edge with a given flow (i.e. edge.eval_cost(flow))
            edges_travel_times[edge.name] = edge.eval_cost(link_occupancy[edge.name])
        return edges_travel_times

    def calculate_average_travel_time(self, string_actions):
        # Calculates the individual travel times
        edges_travel_times = self.calculate_edges_travel_times(string_actions)
        results = []
        for driver_index, action in enumerate(string_actions):
            # Calculates travel times for a driver
            travel_times = 0.0
            path = self.drivers[driver_index].od.paths[action][0]  # list of nodes of path
            for edge in path:
                travel_times += edges_travel_times[edge]
            results.append(travel_times)

        return sum(results) / len(string_actions)

    def drivers_per_link(self, driver_string):
        dicti = {}
        for inx, dr in enumerate(driver_string):
            path = self.drivers[inx].od.paths[dr]
            for edge in path[0]:
                if edge in dicti.keys():
                    dicti[edge] += self.group_size
                else:
                    dicti[edge] = self.group_size

        for link in self.freeFlow.keys():
            if link not in dicti.keys():
                dicti[link] = 0
        return dicti


class QlOutput(Output):
    def __init__(self, infos, network_name, print_interval, print_od_pair, print_travel_time,
                 print_drivers_link, print_drivers_route):
        super().__init__(infos, network_name, print_interval, print_od_pair, print_travel_time,
                         print_drivers_link, print_drivers_route)

        self._create_path()
        self._create_filename()
        super().append_tag()
        # Creates folder to create the file
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

        self.output_file = open(self.filename, 'w')
        print(self._create_header(), file=self.output_file)

    def print_step(self, step_number, stepSolution, ql_travel_time):
        """
        Write infos to the output file.
            step_number:int = episode/generation
            step_solution:QL = instance of QL class.
        """
        if step_number % self.print_interval == 0:
            print(str(step_number) + " " + str(ql_travel_time), file=self.output_file, end=" ")

            if self.print_od_pair:
                print(super().build_od_pair_data(super().travel_time_od(stepSolution)),
                      file=self.output_file, end="")

            if self.print_travel_time:
                travel_times = ""
                edges = super().calculate_edges_travel_times(stepSolution)
                for edge in self.infos["edgeNames"]:
                    travel_times += str(edges[edge]) + " "
                print(travel_times.strip(), file=self.output_file, end=" ")

            if self.print_drivers_link:
                drivers = ""
                edges = super().drivers_per_link(stepSolution)
                for edge in self.infos["edgeNames"]:
                    drivers += str(edges[edge]) + " "
                print(drivers.strip(), file=self.output_file, end=" ")

            if self.print_drivers_route:
                TABLE_FILL = utils.clean_od_table(self.infos["ODL"], self.infos["num_routes"])
                for s in range(len(stepSolution)):
                    TABLE_FILL[str(self.infos["drivers"][s].od.origin) +
                               str(self.infos["drivers"][s].od.destination)][stepSolution[s]] += 1
                print(" ", file=self.output_file, end="")
                for key in self.infos["ODL"]:  # Now it prints in the correct order
                    for x in range(len(self.TABLE_FILL[key])):
                        print(str(TABLE_FILL[key][x]), file=self.output_file, end=" ")

            print("", file=self.output_file)

    def _create_path(self):
        """
            Creates the output file path.
        """
        fmt = "./results_gaql_grouped/net_%s/QL/decay%4.3f/alpha%3.2f"
        self.path = fmt.format(self.network_name, self.infos["decay"], self.infos["alpha"])

    def _create_filename(self):
        """
            Creates the output file name.
        """
        self.filename = self.path + '/' + self.network_name + '_k' + str(self.infos["num_routes"])
        self.filename += '_a' + str(self.infos["alpha"]) + '_d' + str(self.infos["decay"])

    def _create_header(self):
        headerstr = "#Parameters:" + "\n#\tAlpha=" + str(self.infos["alpha"])

        if self.infos["action_selection"] == "epsilon":
            headerstr += "\tEpsilon=" + str(self.infos["epsilon"])

        elif self.infos["action_selection"] == "boltzmann":
            headerstr += "\tTemperature=" + str(self.infos["temperature"])

        headerstr += "\n#\tDecay=" + str(self.infos["decay"]) + "\tNumber of drivers="
        headerstr += str(self.infos["num_drivers"]) + "\n#\tGroup size="
        headerstr += str(self.infos["group_size"]) + "\tQL Table init="
        headerstr += str(self.infos["TABLE_INITIAL_STATE"]) + "\n#\tk="
        headerstr += str(self.infos["num_routes"])

        if self.infos["TABLE_INITIAL_STATE"] == "fixed":
            headerstr += "\t\tFixed value=" + str(self.infos["fixed"])
        elif self.infos["TABLE_INITIAL_STATE"] == "random":
            headerstr += "\t\tMax=" + str(self.infos["maxi"]) + "\n#\tMin="
            headerstr += str(self.infos["mini"])

        headerstr += "\n#Episode AVG_TT " + super().nodes_string()
        return headerstr


class GaOutput(Output):
    def __init__(self, infos, network_name, print_interval, print_od_pair, print_travel_time,
                 print_drivers_link, print_drivers_route):
        super().__init__(infos, network_name, print_interval, print_od_pair, print_travel_time,
                         print_drivers_link, print_drivers_route)

        self._create_path()
        self._create_filename()
        super().append_tag()
        # Creates folder to create the file
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

        self.output_file = open(self.filename, 'w')
        print(self._create_header(), file=self.output_file)

    """
    def print_step(self, step_number, stepSolution, output_file, avgTT=None, qlTT=None):
        Write infos to the output file.
            step_number:int = episode/generation
            step_solution:QL = instance of QL class.

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
                output_file.write(" ")
                for keys in self.ODL:  # Now it prints in the correct order
                    for x in range(len(self.TABLE_FILL[keys])):
                        output_file.write(str(self.TABLE_FILL[keys][x]) + " ")

            output_file.write("\n")
    """

    def _create_path(self):
        """
            Creates the output file path.
        """
        fmt = "./results_gaql_grouped/net_%s/GA/pm%4.4f/crossover_%.2f"
        self.path = fmt.format(self.infos["network_name"], self.infos["mutation"],
                               self.infos["crossover"])

    def _create_filename(self):
        """
            Creates the output file name.
        """
        self.filename = self.path + '/' + self.network_name + '_pm' + str(self.infos["mutation"])
        self.filename += '_c' + str(self.infos["crossover"]) + '_e' + str(self.infos["elite"])
        self.filename += '_k' + str(self.infos["num_routes"])

    def _create_header(self):
        headerstr = "#Parameters:" + "\tPopulation=" + str(self.infos["population"]) \
                  + "\n#\tMutation=" + str(self.infos["mutation"]) + "\tCrossover=" \
                  + str(self.infos["crossover"]) + "\n#\tElite=" + str(self.infos["elite"]) \
                  + "\t\tGroup size=" + str(self.infos["group_size"]) + "\n#\tk=" \
                  + str(self.infos["num_routes"]) + "\t\tNumber of drivers=" \
                  + str(super().get_number_drivers())

        headerstr += "\n#Generation AVG_TT " + super().nodes_string()
        return headerstr


class QlGaOutput(GaOutput):
    def __init__(self, infos, network_name, print_interval, print_od_pair, print_travel_time,
                 print_drivers_link, print_drivers_route):
        super().__init__(infos, network_name, print_interval, print_od_pair, print_travel_time,
                         print_drivers_link, print_drivers_route)

        self._create_path()
        self._create_filename()
        super().append_tag()
        # Creates folder to create the file
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

        self.output_file = open(self.filename, 'w')
        print(self._create_header(), file=self.output_file)

    """
    def __print_step(self, step_number, stepSolution, output_file, avgTT=None, qlTT=None):
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
                output_file.write(" ")
                for keys in self.ODL:  # Now it prints in the correct order
                    for x in range(len(self.TABLE_FILL[keys])):
                        output_file.write(str(self.TABLE_FILL[keys][x]) + " ")

            output_file.write("\n")
    """

    def _create_path(self):
        """
            Creates the output file path.
        """
        fmt = "./results_gaql_grouped/net_%s/QLGA/pm%4.4f/crossover_%.2f/decay%4.3f/alpha%3.2f"
        self.path = fmt.format(self.infos["network_name"], self.infos["mutation"],
                               self.infos["crossover"], self.infos["decay"], self.infos["alpha"])

    def _create_filename(self):
        """
            Creates the output file name.
        """
        super().create_filename()
        self.filename += '_a' + str(self.infos["alpha"]) + '_d' + str(self.infos["decay"])

    def _create_header(self):
        headerstr = "#Parameters:" + "\tPopulation=" + str(self.infos["population"]) \
                  + "\n#\tMutation=" + str(self.infos["mutation"]) + "\tCrossover=" \
                  + str(self.infos["crossover"]) + "\n#\tElite=" + str(self.infos["elite"]) \
                  + "\t\tGroup size=" + str(self.infos["group_size"]) + "\n#\tk=" \
                  + str(self.infos["num_routes"]) + "\t\tNumber of drivers=" \
                  + str(super().get_number_drivers())
        headerstr += "\n#\tAlpha=" + str(self.infos["alpha"]) + "\tDecay=" + str(self.infos["decay"])

        if self.infos["action_selection"] == "epsilon":
            headerstr += "\tEpsilon=" + str(self.infos["epsilon"])

        elif self.infos["action_selection"] == "boltzmann":
            headerstr += "\tTemperature=" + str(self.infos["temperature"])

        headerstr += "\tQL table init=" + str(self.infos["TABLE_INITIAL_STATE"])
        if self.infos["TABLE_INITIAL_STATE"] == "fixed":
            headerstr += "\t\tFixed value=" + str(self.infos["fixed"])
        elif self.infos["TABLE_INITIAL_STATE"] == "random":
            headerstr += "\t\tMax=" + str(self.infos["maxi"]) + "\n#\tMin=" + str(self.infos["mini"])

        headerstr += "\n#Generation AVG_TT QL_AVG_TT" + super().nodes_string()
        return headerstr


class GaQlOutput(QlGaOutput):
    def __init__(self, infos, network_name, print_interval, print_od_pair, print_travel_time,
                 print_drivers_link, print_drivers_route):
        super().__init__(infos, network_name, print_interval, print_od_pair, print_travel_time,
                         print_drivers_link, print_drivers_route)

        self._create_path()
        self._create_filename()
        super().append_tag()
        # Creates folder to create the file
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

        self.output_file = open(self.filename, 'w')
        print(self._create_header(), file=self.output_file)

    """
    def __print_step(self, step_number, stepSolution, output_file, avgTT=None, qlTT=None):
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
                output_file.write(" ")
                for keys in self.ODL:  # Now it prints in the correct order
                    for x in range(len(self.TABLE_FILL[keys])):
                        output_file.write(str(self.TABLE_FILL[keys][x]) + " ")

            output_file.write("\n")
    """

    def _create_path(self):
        """
            Creates the output file path.
        """
        fmt = "./results_gaql_grouped/net_%s/GAQL/pm%4.4f/crossover_%.2f/decay%4.3f/alpha%3.2f"
        self.path = fmt.format(self.infos["network_name"], self.infos["mutation"],
                               self.infos["crossover"], self.infos["decay"], self.infos["alpha"])

    def _create_filename(self):
        """
            Creates the output file name.
        """
        super().create_filename()
        self.filename += '_interval' + str(self.infos["interval"])

    def _create_header(self):
        headerstr = "#Parameters:" + "\tPopulation=" + str(self.infos["population"]) \
                  + "\n#\tMutation=" + str(self.infos["mutation"]) + "\tCrossover=" \
                  + str(self.infos["crossover"]) + "\n#\tElite=" + str(self.infos["elite"]) \
                  + "\t\tGroup size=" + str(self.infos["group_size"]) + "\n#\tk=" \
                  + str(self.infos["num_routes"]) + "\t\tNumber of drivers=" \
                  + str(super().get_number_drivers())
        headerstr += "\n#\tAlpha=" + str(self.infos["alpha"]) + "\tDecay=" + str(self.infos["decay"])

        if self.infos["action_selection"] == "epsilon":
            headerstr += "\tEpsilon=" + str(self.infos["epsilon"])

        elif self.infos["action_selection"] == "boltzmann":
            headerstr += "\tTemperature=" + str(self.infos["temperature"])

        headerstr += "\tQL table init=" + str(self.infos["TABLE_INITIAL_STATE"])
        if self.infos["TABLE_INITIAL_STATE"] == "fixed":
            headerstr += "\t\tFixed value=" + str(self.infos["fixed"])
        elif self.infos["TABLE_INITIAL_STATE"] == "random":
            headerstr += "\t\tMax=" + str(self.infos["maxi"]) + "\n#\tMin=" + str(self.infos["mini"])

        headerstr += "\n#\tGA<->QL interval=" + str(self.infos["interval"])

        headerstr += "\n#Generation AVG_TT QL_AVG_TT" + super().nodes_string()
        return headerstr
