import heapq
import itertools
import json

from direct.stdpy.file import exists, open
from panda3d.core import PNMImage

OBSTACLE = -10
DESTINATION = -2
UNINITIALIZED = -1

WALL = OBSTACLE
FREE = UNINITIALIZED


class FoundPath(Exception):
    """ Raise this when you found a path. it's not really an error,
    but I need to stop the program and pass it up to the real function"""
    pass


class FastPriorityQueue:
    """
    A faster queue than queue.PriorityQueue
    Implementation copied from: https://docs.python.org/3.3/library/heapq.html
    """

    def __init__(self):
        self.pq = []  # list of entries arranged in a heap
        self.counter = itertools.count()  # unique sequence count

    def add_task(self, task, priority=0):
        'Add a new task'
        count = next(self.counter)
        entry = [priority, count, task]
        heapq.heappush(self.pq, entry)

    def pop_task(self):
        """Remove and return the lowest priority task. Raise KeyError if empty."""
        while self.pq:
            priority, count, task = heapq.heappop(self.pq)
            return task
        raise KeyError('pop from an empty priority queue')

    def empty(self):
        return len(self.pq) == 0


def _getPath(sources, start_x, start_y, end_x, end_y):
    """
    Reconstruct the path from the source information as given by jps(...).

    Parameters
    sources          - a 2d array of the predecessor to each node
    start_x, start_y - the x, y coordinates of the starting position
    end_x, end_y     - the x, y coordinates of the destination

    Return
    a list of jump points as 2-tuples (coordinates) starting from the start node and finishing at the end node.
    """
    result = []
    cur_x, cur_y = end_x, end_y

    while cur_x != start_x or cur_y != start_y:
        result.append((cur_x, cur_y))
        cur_x, cur_y = sources[cur_x][cur_y]
    result.reverse()
    return [(start_x, start_y)] + result


class Pathfinder:
    def __init__(self):

        # the map
        self.nav_map = None

    def _exploreDiagonal(self, startX, startY, directionX, directionY):
        """
        Explores field along the diagonal direction for JPS, starting at point (startX, startY)

        Parameters
        startX, startY - the coordinates to start exploring from. 
        directionX, directionY - an element from: {(1, 1), (-1, 1), (-1, -1), (1, -1)} corresponding to the x and y directions respectively. 

        Return
        A 2-tuple containing the coordinates of the jump point if it found one
        None if no jumppoint was found. 
        """
        cur_x, cur_y = startX, startY  # indices of current cell.
        curCost = self.field[startX][startY]

        while True:
            cur_x += directionX
            cur_y += directionY
            curCost += 1

            if self.field[cur_x][cur_y] == UNINITIALIZED:
                self.field[cur_x][cur_y] = curCost
                self.sources[cur_x][cur_y] = startX, startY
            elif cur_x == self.end_x and cur_y == self.end_y:  # destination found
                self.field[cur_x][cur_y] = curCost
                self.sources[cur_x][cur_y] = startX, startY
                raise FoundPath()
            else:  # collided with an obstacle. We are done.
                return None

            # If a jump point is found, 
            if self.field[cur_x + directionX][cur_y] == OBSTACLE and self.field[cur_x + directionX][
                cur_y + directionY] != OBSTACLE:
                return cur_x, cur_y
            else:  # otherwise, extend a horizontal "tendril" to probe the field.
                self._queueJumpPoint(self._exploreCardinal(cur_x, cur_y, directionX, 0))

            if self.field[cur_x][cur_y + directionY] == OBSTACLE and self.field[cur_x + directionX][
                cur_y + directionY] != OBSTACLE:
                return cur_x, cur_y
            else:  # extend a vertical search to look for anything
                self._queueJumpPoint(self._exploreCardinal(cur_x, cur_y, 0, directionY))

    def _exploreCardinal(self, startX, startY, directionX, directionY):
        """
        Explores field along a cardinal direction for JPS (north/east/south/west), starting at point (startX, startY)

        Parameters
        startX, startY - the coordinates to start exploring from. 
        directionX, directionY - an element from: {(1, 1), (-1, 1), (-1, -1), (1, -1)} corresponding to the x and y directions respectively. 

        Result: 
        A 2-tuple containing the coordinates of the jump point if it found one
        None if no jumppoint was found.
        """
        cur_x, cur_y = startX, startY  # indices of current cell.
        curCost = self.field[startX][startY]

        while True:
            cur_x += directionX
            cur_y += directionY
            curCost += 1

            if self.field[cur_x][cur_y] == UNINITIALIZED:
                self.field[cur_x][cur_y] = curCost
                self.sources[cur_x][cur_y] = startX, startY
            elif cur_x == self.end_x and cur_y == self.end_y:  # destination found
                self.field[cur_x][cur_y] = curCost
                self.sources[cur_x][cur_y] = startX, startY
                raise FoundPath()
            else:  # collided with an obstacle or previously explored part. We are done.
                return None

            # check neighbouring cells, i.e. check if cur_x, cur_y is a jump point.
            if directionX == 0:
                if self.field[cur_x + 1][cur_y] == OBSTACLE and self.field[cur_x + 1][cur_y + directionY] != OBSTACLE:
                    return cur_x, cur_y
                if self.field[cur_x - 1][cur_y] == OBSTACLE and self.field[cur_x - 1][cur_y + directionY] != OBSTACLE:
                    return cur_x, cur_y
            elif directionY == 0:
                if self.field[cur_x][cur_y + 1] == OBSTACLE and self.field[cur_x + directionX][cur_y + 1] != OBSTACLE:
                    return cur_x, cur_y
                if self.field[cur_x][cur_y - 1] == OBSTACLE and self.field[cur_x + directionX][cur_y - 1] != OBSTACLE:
                    return cur_x, cur_y

    def _queueJumpPoint(self, xy):
        """
        Add a jump point to the priority queue to be searched later. The priority is the minimum possible number of steps to the destination. 
        Also check whether the search is finished.

        Parameters
        self.queue - a priority queue for the jump point search
        xy - 2-tuple with the coordinates of a point to add.

        Return
        None
        """
        if xy is not None:
            self.queue.add_task(xy, self.field[xy[0]][xy[1]] + max(abs(xy[0] - self.end_x), abs(xy[1] - self.end_y)))

    def loadMap(self, map_file):
        # the map_file can be just a list
        if type(map_file) is list:
            self.nav_map = map_file
        # it can also be a file
        elif exists(map_file):
            # ...a json file?
            try:
                with open(map_file) as f:
                    self.nav_map = json.load(f)
            except:
                # ...an image?
                try:
                    img = PNMImage(map_file)
                    max_x = img.getReadXSize()
                    max_y = img.getReadYSize()
                    temp_map = [[WALL for x in range(max_x)] for x in range(max_y)]
                    for x in range(max_x):
                        for y in range(max_y):
                            if img.getRedVal(x, y) < 0.5:
                                temp_map[x][max_y - 1 - y] = FREE
                    self.nav_map = temp_map
                except:
                    print("Can't load map!")

    def saveMap(self, name):
        if self.nav_map:
            with open(name, 'w') as outfile:
                json.dump(self.nav_map, outfile)

    def getPath(self, start, end):
        if self.nav_map:
            self.field = [[j for j in i] for i in self.nav_map]  # this takes less time than deep copying(?)        
            self.start_x = int(start[0])
            self.start_y = int(start[1])
            self.end_x = int(end[0])
            self.end_y = int(end[1])

            # handle obvious exception cases: either start or end is unreachable
            if self.field[self.start_x][self.start_y] == OBSTACLE:
                return None
            if self.field[self.end_x][self.end_y] == OBSTACLE:
                return None

            # MAIN JPS FUNCTION           
            # Initialize some arrays and certain elements. 
            self.sources = [[(None, None) for i in self.field[0]] for j in
                            self.field]  # the jump-point predecessor to each point.
            self.field[self.start_x][self.start_y] = 0
            self.field[self.end_x][self.end_y] = DESTINATION

            self.queue = FastPriorityQueue()
            self._queueJumpPoint((self.start_x, self.start_y))

            # Main loop: iterate through the queue
            while not self.queue.empty():
                pX, pY = self.queue.pop_task()

                try:
                    self._queueJumpPoint(self._exploreCardinal(pX, pY, 1, 0))
                    self._queueJumpPoint(self._exploreCardinal(pX, pY, -1, 0))
                    self._queueJumpPoint(self._exploreCardinal(pX, pY, 0, 1))
                    self._queueJumpPoint(self._exploreCardinal(pX, pY, 0, -1))

                    self._queueJumpPoint(self._exploreDiagonal(pX, pY, 1, 1))
                    self._queueJumpPoint(self._exploreDiagonal(pX, pY, 1, -1))
                    self._queueJumpPoint(self._exploreDiagonal(pX, pY, -1, 1))
                    self._queueJumpPoint(self._exploreDiagonal(pX, pY, -1, -1))
                except FoundPath:
                    return _getPath(self.sources, self.start_x, self.start_y, self.end_x, self.end_y)
            return None
        return None
