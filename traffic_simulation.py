from config import ExperimentConfig as cfg
import config
import argparse

p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                            description="""Script to run the simulation of
                            drivers going from different points in the ortuzar
                            and siouxfalls networks""")

p.add_argument("--printTravelTime", action="store_true", default=False,
               help="Print link's travel time at each iteration in the output file")

p.add_argument("-d", "--printDriversPerLink", action="store_true", default=False,
               help="Print the number of drivers in each link in the output file")

p.add_argument("-o", "--printPairOD", action="store_true", default=False,
               help="Print the average travel time for in the header in the output file")

p.add_argument("-i", "--printInterval", type=int, default=1,
               help="Interval by which the messages are written in the output file")

p.add_argument("-g", "--generations", type=int, default=400,
               help="Maximum mumber of generations in each configuration")

p.add_argument("-p", "--population", type=int, default=100,
               help="Size of population for the genetic algorithm")

p.add_argument("--grouping", nargs="+", type=int, default=[100],
               help="List of group sizes for drivers in each configuration")

p.add_argument("-a", "--alphas", nargs="+", type=float, default=[.9],
               help="List of learning rates in each configuration")

p.add_argument("--decays", nargs="+", type=float, default=[.99],
               help="List of decays in each configuration")

p.add_argument("-c", "--crossovers", nargs="+", type=float, default=[0.2],
               help="List of rate of crossover in the population in each configuration")

p.add_argument("-m", "--mutations", nargs="+", type=float, default=[0.001],
               help="List of rate of mutations in each configuration")

p.add_argument("--ks", nargs="+", type=int, default=[8],
               help="List of the 'K' hyperparameters for the KSP (K-ShortestPath) Algorithm")

p.add_argument("--intervals", nargs="+", type=int, default=[None],
               help="List of intervals that signal the frequency the QL values are supposed to be fed into GA")

p.add_argument("--repetitions", type=int, default=1,
               help="How many times it should be repeated")

p.add_argument("--net", type=unicode, choices=['OW10_1', 'SF'], default='OW10_1',
               help="Which network should be used")

p.add_argument("--experimentType", type=int, choices=[1,2,3,4], default=1,
               help="""
               1 - QL only
               2 - GA only
               3 - QL builds solution for GA
               4 - GA and QL exchange solutions
               """)

p.add_argument("-e", "--elite_size", type=int, default=5,
               help="How many elite individuals should be kept after each generation")

p.add_argument("--number-of-processes", type=int, default=1,
               help="How many parallel processes should be used to run the experiment configurations")

a = p.parse_args()

networks = {
  'OW10_1': (config.ORTUZAR_NETWORK, config.ORTUZAR_NETWORK_OD),
  'SF': (config.SIOUXFALLS_NETWORK, config.SIOUXFALLS_NETWORK_OD)
}

configuration = cfg(printTravelTime=a.printTravelTime, printDriversPerLink=a.printDriversPerLink,
             printPairOD=a.printPairOD, generations=a.generations,
             population=a.population, repetitions=a.repetitions,
             experimentType=a.experimentType, elite_size=a.elite_size,
             group_sizes=a.group_sizes, alphas=a.alphas, decays=a.decays,
             crossovers=a.crossovers, mutations=a.mutations, ks=a.ks,
             interval=a.intervals, network_od=networks[a.network][1],
             network=networks[a.network][0], printInterval=a.printInterval)

configuration.run(number_of_processes=a.number_of_processes)

