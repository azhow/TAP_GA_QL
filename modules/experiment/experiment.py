#!/usr/bin/env python
"""
This module contains the Experiment class, which is the experiment or simulation itself.

Warning: Use spaces instead of tabs, or configure your editor to transform tab to 4 spaces.
"""

# Standard modules
import os
import string

# Local modules
import modules.q_learning.q_learning as q_learning
import modules.functions.functions as utils
import modules.experiment.classes as classes
import ksp.KSP as ksp


class Experiment(object):
    def __init__(self, k, net_file, group_size, table_fill_file=None,
                 flow=0, epsilon=1.0, TABLE_INITIAL_STATE='fixed',
                 MINI=0.0, MAXI=0.0, fixed=0.0, action_selection="epsilon", temperature=0.0):

        '''
            Construct the experiment.
        '''

        self.action_selection = action_selection
        self.temperature = temperature
        self.k = k
        self.epsilon = epsilon
        self.group_size = group_size

        self.ODheader = ""
        self.ODL = []

        self.TABLE_INITIAL_STATE = TABLE_INITIAL_STATE
        self.flow = flow
        self.TABLE_FILL = {}
        self.mini = MINI
        self.maxi = MAXI
        self.fixed = fixed
        self.ODlist = []

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


if __name__ == '__main__':
    """"
    To run the tests you should call from the terminal: python Experiment.py

    If the tests succeed, nothing should happen.  Else it will show the error
    and where it is on the file.
    """
    import doctest
    doctest.testmod()
