import re
import sys
from queue import PriorityQueue
from math import *
from PIL import Image

class Node:

    __slots__ = 'x', 'y', 'z', 'adjacent', 'terrain'

    def __init__(self, x, y, z = None, terrain = None):
        self.x = x
        self.y = y
        self.z = z
        self.terrain = terrain
        self.adjacent = dict()

    def addAdjacent(self, nbr, cost):
        self.adjacent[nbr] = cost

    def keysAdjacent(self):
        return self.adjacent.keys()

    def __lt__(self, other):
        return self.x == other.x and self.y < other.y

class Graph:

    __slots__ = 'pointsList', 'numVertices', 'speed_dict', 'season', 'pixelsWater'

    def __init__(self, allPixels, elevations, widthFinal, lengthFinal, season):
        self.pointsList = {}
        self.pixelsWater = []
        self.numVertices = 0
        self.speed_dict = {(248, 148, 18): 1.5, (255, 192, 0): 1.2, (255, 255, 255): 1.4, (2, 208, 60): 1.1,
                           (2, 136, 40): 1, (5, 73, 24): 0.2, (0, 0, 255): 0.15, (71, 51, 3): 1.7, (0, 0, 0): 1.55,
                           (205, 0, 101): 0.0001, (139, 69, 19): 0.9, (163, 208, 212): 0.9}
        if season == 'fall':
            self.speed_dict[255, 255, 255] = 1.10
        self.season = season
        changeFlag = False
        if self.season == 'winter' or self.season == 'spring':
            changeFlag = True
        landFlag = False
        waterFlag = False
        for x in range(widthFinal):
            for y in range(lengthFinal):
                if allPixels[x][y] == (0, 0, 255):
                    waterFlag = True
                    landFlag = False
                if x - 1 >= 0 and y - 1 >= 0:
                    if waterFlag and changeFlag and allPixels[x - 1][y - 1] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x - 1, y - 1, elevations, allPixels)
                if x - 1 >= 0:
                    if waterFlag and changeFlag and allPixels[x - 1][y] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x - 1, y, elevations, allPixels)
                if y - 1 >= 0:
                    if waterFlag and changeFlag and allPixels[x][y - 1] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x, y - 1, elevations, allPixels)
                if landFlag and changeFlag and waterFlag:
                    self.pixelsWater.append((x, y))
                    waterFlag = False
                if x + 1 < widthFinal:
                    if waterFlag and changeFlag and allPixels[x + 1][y] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x + 1, y, elevations, allPixels)
                if x + 1 < widthFinal and y - 1 >= 0:
                    if waterFlag and changeFlag and allPixels[x + 1][y - 1] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x + 1, y - 1, elevations, allPixels)
                if x - 1 >= 0 and y + 1 < lengthFinal:
                    if waterFlag and changeFlag and allPixels[x - 1][y + 1] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x - 1, y + 1, elevations, allPixels)
                if y + 1 < lengthFinal:
                    if waterFlag and changeFlag and allPixels[x][y + 1] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x, y + 1, elevations, allPixels)
                if x + 1 < widthFinal and y + 1 < lengthFinal:
                    if waterFlag and changeFlag and allPixels[x + 1][y + 1] != (0, 0, 255):
                        landFlag = True
                    self.side(x, y, x + 1, y + 1, elevations, allPixels)

    def __iter__(self):
        return iter(self.pointsList.values())

    def addPoint(self, node):
        if self.getPixel((node.x, node.y)) is None:
            self.numVertices += 1
            self.pointsList[(node.x, node.y)] = node
        return node

    def getPixel(self, key):
        if key in self.pointsList:
            return self.pointsList[key]
        else:
            return None

    def side(self, startx, starty, finalx, finaly, elevations, pix):
        startz = elevations[startx][starty]
        finalz = elevations[finalx][finaly]
        if (startx, starty, startz) not in self.pointsList:
            self.addPoint(Node(startx, starty, startz, pix[startx][starty]))
        if (finalx, finaly, finalz) not in self.pointsList:
            self.addPoint(Node(finalx, finaly, finalz, pix[finalx][finaly]))
            radians = (finalz - startz) / sqrt((((finalx - startx) * 10.29) ** 2) + (((finaly - starty) * 7.55) ** 2))
            multiplier = 1
            if radians < 0 or radians > 0:
                multiplier = cos(atan(radians))
                if radians < 0:
                    multiplier = 2 * multiplier
            cost = sqrt((((finalx - startx) * 10.29) ** 2) + (((finaly - starty) * 7.55) ** 2)) / (
                        self.speed_dict[self.pointsList[(finalx, finaly)].terrain] * multiplier)
            self.pointsList[(startx, starty)].addAdjacent(self.pointsList[(finalx, finaly)], cost)

    def __contains__(self, key):
        return key in self.pointsList

def terrainBasedSeason(pixelsWater, graph, season, speed_dict):
    if season == 'summer' or 'fall' or 'winter' or 'spring':
        seasonal_depth_change = 0
        if season == 'winter':
            seasonal_depth_change = 7
        elif season == 'spring':
            seasonal_depth_change = 15
    points = []
    for pixel in pixelsWater:
        start = graph.getPixel((pixel[0], pixel[1]))
        if start.terrain == (0, 0, 255):
            listVisited = set()
            winterFlag = False
            springFlag = False
            if season == 'spring':
                newColour = (160, 75, 40)
                elevation = start.z
                springFlag = True
            elif season == 'winter':
                newColour = (163, 208, 212)
                start.terrain = (163, 208, 212)
                winterFlag = True
                listVisited.add((start.x, start.y))
            layer = 1
            lists = [start]
            while layer <= seasonal_depth_change and len(lists) > 0:
                node = lists.pop(0)
                for adj in node.keysAdjacent():
                    if (adj.x, adj.y) not in listVisited:
                        if ((winterFlag and adj.terrain == (0, 0, 255)) or (springFlag and adj.terrain != (0, 0, 255) and (adj.z - elevation < 1))):
                            lists.append(adj)
                            listVisited.add((adj.x, adj.y))
                            adj.terrain = newColour

                            radians = (adj.z - node.z) / sqrt(
                                (((adj.x - node.x) * 10.29) ** 2) + (((adj.y - node.y) * 7.55) ** 2))
                            multiplier = 1
                            if radians != 0:
                                multiplier = cos(atan(radians))
                                if radians < 0:
                                    multiplier = 2 * multiplier
                            cost = sqrt((((adj.x - node.x) * 10.29) ** 2) + (((adj.y - node.y) * 7.55) ** 2)) / (
                                        speed_dict[graph.pointsList[(adj.x, adj.y)].terrain] * multiplier)
                            node.addAdjacent(adj, cost)
                layer += 1
            points.append(list(listVisited))
    return points

def search(start, final, speed_dict):
    priorq = PriorityQueue()
    priorq.put((sqrt((((final.x - start.x) * 10.29) ** 2) + (((final.y - start.y) * 7.55) ** 2) + ((final.z - start.z) ** 2)) / speed_dict[(71, 51, 3)], (start, None)))
    seen = set()
    origin = {}
    costTot = {}
    while not priorq.empty():
        min_node_cost_tuple = priorq.get()
        min_node_tuple = min_node_cost_tuple[1]
        first = min_node_tuple[0]
        origin[(first.x, first.y)] = min_node_tuple[1]
        cost = min_node_cost_tuple[0] - (sqrt((((final.x - first.x) * 10.29) ** 2) + (((final.y - first.y) * 7.55) ** 2) + ((final.z - first.z) ** 2)) / speed_dict[(71, 51, 3)])
        costTot[first] = cost
        if (first.x, first.y) in seen:
            continue
        if first.x == final.x and first.y == final.y:
            seen.add((first.x, first.y))
            return origin, costTot
        seen.add((first.x, first.y))
        for adj in first.keysAdjacent():
            if (adj.x, adj.y) not in seen:
                priorq.put((
                    cost + first.adjacent[adj] + (sqrt((((final.x - adj.x) * 10.29) ** 2) + (((final.y - adj.y) * 7.55) ** 2) + ((final.z - adj.z) ** 2)) / speed_dict[(71, 51, 3)]),
                    (adj, (first.x, first.y))))
    return origin, costTot


def main():
    terrain = sys.argv[1]
    elevation = sys.argv[2]
    path = sys.argv[3]
    season = sys.argv[4]
    resultImg = sys.argv[5]

    speed_dict = {(248, 148, 18): 1.5, (255, 192, 0): 1.2, (255, 255, 255): 1.4, (2, 208, 60): 1.1,
                       (2, 136, 40): 1, (5, 73, 24): 0.2, (0, 0, 255): 0.15, (71, 51, 3): 1.7, (0, 0, 0): 1.45,
                       (205, 0, 101): 0.0001, (160, 75, 40): 0.9, (163, 208, 212): 0.9}
    if season == 'fall':
        speed_dict[255, 255, 255] = 1.10

    wideElev = 395
    lenghthElev = 500
    elevations = [[0 for x in range(lenghthElev)] for x in range(wideElev)]
    with open(elevation) as f:
        counter = 0
        for line in f.readlines():
            column = 0
            lineSplit = re.split('[\s]+', line.strip())
            for elevNumber in lineSplit:
                if column < 395:
                    elevations[column][counter] = float(elevNumber)
                column += 1
            counter += 1

    pixelLocation = []
    image = Image.open(terrain)
    pixels = image.load()
    outputImg = image.copy()
    pixelOutputImage = outputImg.load()
    widthImage = image.size[0]
    heightImage = image.size[1]
    allPixels = [[(0, 0, 0) for x in range(heightImage)] for x in
                  range(widthImage)]

    for i in range(widthImage):
        for j in range(heightImage):
            pixelRGB = pixels[i, j][0:3]
            allPixels[i][j] = pixelRGB

    graph = Graph(allPixels, elevations, wideElev, lenghthElev, season)
    pixelChange = terrainBasedSeason(graph.pixelsWater, graph, season, speed_dict)
    if season == 'winter':
        changed_terrain = (163, 208, 212, 255)
    elif season == 'spring':
        changed_terrain = (160, 75, 40, 255)
    for pix in pixelChange:
        for j in pix:
            pixelOutputImage[j[0], j[1]] = changed_terrain
    with open(path) as f:
        for line in f.readlines():
            pixelLocation.append(tuple(map(int, line.strip().split(' '))))
    for point in pixelLocation:
        x = point[0]
        y = point[1]
        if x - 1 >= 0 and y - 1 >= 0:
            pixelOutputImage[x - 1, y - 1] = (200, 133, 25, 255)
        if x + 1 < widthImage and y + 1 < heightImage:
            pixelOutputImage[x + 1, y + 1] = (200, 133, 25, 255)
        if x - 1 >= 0:
            pixelOutputImage[x - 1, y] = (5, 5, 25, 255)
        if y - 1 >= 0:
            pixelOutputImage[x, y - 1] = (5, 5, 25, 255)
        if x + 1 < widthImage:
            pixelOutputImage[x + 1, y] = (5, 5, 25, 255)
        if y + 1 < heightImage:
            pixelOutputImage[x, y + 1] = (5, 5, 25, 255)
        if x + 1 < widthImage and y - 1 >= 0:
            pixelOutputImage[x + 1, y - 1] = (5, 5, 25, 255)
        if x - 1 >= 0 and y + 1 < heightImage:
            pixelOutputImage[x - 1, y + 1] = (5, 5, 25, 255)

    index = 0
    outputPixel = []
    total_cost = 0
    total_distance = 0
    while index + 1 < len(pixelLocation):
        came_from, cost = search(graph.getPixel(pixelLocation[index]), graph.getPixel(pixelLocation[index + 1]), speed_dict)
        start = pixelLocation[index + 1]
        i = []
        i.insert(0, start)
        while came_from[start] is not None:
            source = start
            end = came_from[start]
            total_cost = total_cost + cost[graph.getPixel(end)]
            total_distance = total_distance + sqrt(
                (((end[0] - source[0]) * 10.29) ** 2) + (((end[1] - source[1]) * 7.55) ** 2) + ((elevations[end[0]][end[1]] - elevations[source[0]][source[1]]) ** 2))
            i.insert(0, end)
            start = end
        outputPixel.append(i)
        index += 1
    print("Best Track Distance:\t" + str(total_distance))
    for i in outputPixel:
        for j in i:
            pixelOutputImage[j[0], j[1]] = (128, 0, 128, 255)
    outputImg.save(resultImg)

main()