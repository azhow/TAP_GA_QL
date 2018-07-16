#!/usr/bin/env python
"""
This module contains the Experiment class, which is the experiment or simulation itself.

Warning: Use spaces instead of tabs, or configure your editor to transform tab to 4 spaces.
"""

#Standard modules
import os
import string

#Local modules
import modules.q_learning.q_learning as q_learning
import modules.functions.functions as utils
import modules.experiment.classes as classes
import ksp.KSP as ksp


class Experiment(object):
    '''
        Sets up an experiment.
    '''
    def __init__(self, k, net_file, group_size, net_name, table_fill_file=None,
                 flow=0, p_travel_time=False, p_drivers_link=False, p_od_pair=False, p_interval=1,
                 epsilon=1.0, p_drivers_route=False, TABLE_INITIAL_STATE='fixed',
                 MINI=0.0, MAXI=0.0, fixed=0.0, action_selection="epsilon", temperature=0.0,
                 ):

        '''
            Construct the experiment.
        '''

        self.action_selection = action_selection
        self.temperature = temperature
        self.k = k
        self.epsilon = epsilon
        self.group_size = group_size
        self.printDriversPerLink = p_drivers_link
        self.printTravelTime = p_travel_time
        self.printODpair = p_od_pair
        self.printInterval = p_interval
        self.printDriversPerRoute = p_drivers_route
        self.TABLE_INITIAL_STATE = TABLE_INITIAL_STATE
        self.network_name = net_name
        self.flow = flow
        self.TABLE_FILL = {}
        self.mini = MINI
        self.maxi = MAXI
        self.fixed = fixed
        self.ODlist = []
        self.ODL = []
        self.ODheader = ""

        self.Vo, self.Eo, odInputo = utils.read_infos(net_file, flow=flow)

        for tup_od in odInputo:
            if round(tup_od[2]) % self.group_size != 0:
                print tup_od[2]
                raise Exception("Error: number of travels is not a multiple \
                                 of the group size origin: " + str(tup_od[0])
                                + " destination: " + str(tup_od[1]))
            else:
                #Origin, destination, number of paths, number of travels
                self.ODlist.append(classes.OD(tup_od[0], tup_od[1],
                                      k, tup_od[2] / self.group_size))
                self.ODL.append(str(tup_od[0]) + str(tup_od[1]))
                for i in range(k):
                    if len(self.ODheader) == 0:
                        self.ODheader = self.ODheader + str(tup_od[0]) + "to" + str(tup_od[1]) \
                                      + "_" + str(i + 1)
                    else:
                        self.ODheader = self.ODheader + " " + str(tup_od[0]) + "to" \
                                      + str(tup_od[1]) + "_" + str(i + 1)

        #Get the k shortest routes
        for od_pair in self.ODlist:
            od_pair.paths = ksp.getKRoutes(self.Vo, self.Eo, od_pair.o, od_pair.d, od_pair.numPaths)

        ##get the value of each link - free flow travel time
        self.freeFlow = {}
        for edge in self.Eo:
            self.freeFlow[edge.name] = edge.cost

        self.edgeNames = sorted(self.freeFlow.keys())

        #creates different drivers according to the number of travels of each OD
        #instance
        self.drivers = []
        for od_pair in self.ODlist:
            for i in range(int(round(od_pair.numTravels))):
                self.drivers.append(classes.Driver(od_pair))

        if TABLE_INITIAL_STATE == 'coupling':
            self.TABLE_FILL = utils.generate_table_fill(table_fill_file)

    def __repr__(self):
        """
        __repr__ method override.

        >>> Experiment(8, './networks/OW10_1/OW10_1.net', 1, 'OW10_1')
        'Experiment: k = 8, net_name = OW10_1'
        """
        return repr(str('Experiment: k = ' + str(self.k) + ', net_name = ' + (self.network_name)))

    def genCallBack(self, ga_engine):
        """
        GA stuff. Not ready for it yet, assuming it is working as it should.
        """
        population = ga_engine.getPopulation()
        generation = ga_engine.getCurrentGeneration()
        if self.printDriversPerRoute:
            #Drivers per route
            for od in self.ODL:
                self.TABLE_FILL[str(od)] = [0] * self.k

        #gets worst individual
        worstsol = population[len(population) - 1]

        if self.useQL:  # if using QL
            #check if the GA->QL interval is None
            if self.interval is None:
                isGeneration = 1
            else:
                isGeneration = (generation + 1) % self.interval

            #check if we are running the GA<->QL or GA<-QL experiment.
            if self.useInterval and (isGeneration == 0) and (generation != 0):
                (qlind, avg_tt) = \
                    self.ql.runEpisodeWithAction(ga_engine.bestIndividual().getInternalList())
                    #GA->QL
            else:
                (qlind, avg_tt) = self.ql.runEpisode()  # GA<-QL
                #qlind is a array of paths taken by each driver

            #for each driver
            for i in range(len(qlind)):
                worstsol.getInternalList()[i] = qlind[i]
            worstsol.evaluate()

            #if worstscore has a smaller average travel time than the
            #best individual, copies the ql solution (worstscore)
            #to the second best individual
            if worstsol.score < ga_engine.bestIndividual().score:
                print(">>>>> QL indiv. "+ str(worstsol.score), "turned better than best ind. "
                      + str(ga_engine.bestIndividual().score)+ "at generation "+ str(generation))
                #copies QL solution to 2nd best ind.
                worstsol.copy(ga_engine.getPopulation()[1])
                ga_engine.getPopulation()[1].evaluate()
            else:
                #copies QL solution to worst in population
                worstsol.copy(ga_engine.getPopulation()[1])
                ga_engine.getPopulation()[len(population) - 1].evaluate()

        self.__print_step(generation, ga_engine.bestIndividual().getInternalList(),
                          avgTT=ga_engine.bestIndividual().score, qlTT=worstsol.score)

    def run_ql(self, num_episodes, alpha, decay):
        self.useGA = False
        self.useQL = True
        self.alpha = alpha
        self.decay = decay
        self.ql = q_learning.QL(self, self.drivers, self.k, self.decay, self.alpha, self.TABLE_FILL,
                     self.epsilon, self.TABLE_INITIAL_STATE, MINI=self.mini, MAX=self.maxi,
                     fixed=self.fixed, action_selection=self.action_selection,
                     temperature=self.temperature)

        for episode in range(num_episodes):
            (instance, value) = self.ql.runEpisode()
            self.__print_step(episode, instance, qlTT=value)
        ''' To print progress bar, uncomment this line.
            print_progress(episode+1, num_episodes)
        '''

    def run_ga_ql(self, useQL, useInt, generations, population, crossover, mutation, elite, alpha,
                  decay, interval):
        from modules.genetic_algorithm.genetic_algorithm import *
        self.useGA = True
        self.useQL = useQL
        self.useInterval = useInt
        self.interval = interval
        self.generations = generations
        self.population = population
        self.crossover = crossover
        self.mutation = mutation
        self.elite = elite
        self.alpha = alpha
        self.decay = decay
        if(useQL):
            self.ql = q_learning.QL(self, self.drivers, self.k, self.decay, self.alpha, self.TABLE_FILL,
                         self.epsilon, self.TABLE_INITIAL_STATE, MINI=self.mini, MAX=self.maxi,
                         fixed=self.fixed, action_selection=self.action_selection,
                         temperature=self.temperature)

        filename, path, headerstr = self.createStringArguments(useQL, useInt)
        filename = utils.appendTag(filename)

        ##creates file
        if os.path.isdir(path) is False:
            os.makedirs(path)

        self.outputFile = open(filename, 'w')
        self.outputFile.write(headerstr + '\n')

        self.ga = GA(generations, population, crossover, mutation, elite, self,
                     self.genCallBack, self.calculateAverageTravelTime, self.drivers)
        self.ga.evolve()

        print("Output file location: %s" % filename)
        self.outputFile.close()

    def driversPerLink(self, driverString):
        """
        receives an array of ints stresenting the chosen path of each group
        the array is sorted in the same way as the alleles and the drivers
        list
        returns a dicionary where the keys are edges and the values are the
        amount of drivers on the edge
        """
        dicti = {}
        for inx, dr in enumerate(driverString):
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

    def evaluateActionTravelTime(self, driverIndex, action, edgesTravelTimes):
        #calculates travel times for a driver
        traveltime = 0.0
        path = self.drivers[driverIndex].od.paths[action][0]  # list of nodes of path
        for edge in path:
            traveltime += edgesTravelTimes[edge]
        return traveltime

    def initTravelTimeByODDict(self):
        d = {}
        for od in self.ODlist:
            d["%s%s" % (od.o, od.d)] = []
        return d

    def travelTimeByOD(self, string_actions):
        edgesTravelTimes = self.calculate_edges_travel_times(string_actions)
        odTravelTimeDict = self.initTravelTimeByODDict()
        for driverIdx, action in enumerate(string_actions):
            path = self.drivers[driverIdx].od.paths[action][0]
            traveltime = 0.0
            for edge in path:
                traveltime += edgesTravelTimes[edge]
            odTravelTimeDict[self.drivers[driverIdx].od_s()].append(traveltime)

        return odTravelTimeDict

    def calculateIndividualTravelTime(self, string_actions):
        #returns list of travel times for each driver
        edgesTravelTimes = self.calculate_edges_travel_times(string_actions)
        results = []
        for driverIdx, action in enumerate(string_actions):
            travel_times = self.evaluateActionTravelTime(driverIdx, action, edgesTravelTimes)
            results.append(travel_times)
        return results

    def calculate_edges_travel_times(self, string_actions):
        edges_travel_times = {}
        #Get the flow of that edge
        link_occupancy = self.driversPerLink(string_actions)
        #For each edge
        for edge in self.Eo:
            #Evaluates the cost of that edge with a given flow (i.e. edge.eval_cost(flow))
            edges_travel_times[edge.name] = edge.eval_cost(link_occupancy[edge.name])
        return edges_travel_times

    def calculateAverageTravelTime(self, stringOfActions):
        return sum(self.calculateIndividualTravelTime(stringOfActions)) / len(stringOfActions)


if __name__ == '__main__':
    """"
    To run the tests you should call from the terminal: python Experiment.py

    If the tests succeed, nothing should happen.  Else it will show the error
    and where it is on the file.
    """
    import doctest
    doctest.testmod()
