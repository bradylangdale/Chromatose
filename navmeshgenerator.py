import csv
             
from panda3d.core import *

class NavMeshGenerator():
    def __init__(self):
        self.dirname = 'NavMeshes'
        self.basename = 'defaultnavmesh.csv'
        self.gridSize = 10 # default 10x10 grid
        self.xstep = 5
        self.ystep = self.xstep
        self.bottomLeftCorner = LVecBase3f(0, 0, 0)
        self.bitMask = BitMask32().all_off()
        self.scene = None
        
    @property
    def filepath(self):
        return Filename(self.dirname, self.basename)

    def generate(self):
        def gridElement_to_x_y(gridElement):
            xy = gridElement.split('x')
            x = int(xy[0])
            y = int(xy[1])
            return x, y
        
        self.filepath.make_dir()

        size = self.gridSize
        xstep = self.xstep
        ystep = self.ystep
        bottomLeftCorner = LVecBase3f(self.bottomLeftCorner)
        
        with open(self.filepath, 'w') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
            filewriter.writerow(['Grid Size', size])
            filewriter.writerow(['NULL', 'NodeType', 'GridX', 'GridY', 'Length', 'Width', 'Height', 'PosX', 'PosY', 'PosZ'])
            # NodeType 0 = center
            # next 8 nodes are it's neighbours, NULL if they dont exist
            # 0 0
            # 1 -1
            # 1 0
            # 1 1
            # 0 1
            # -1 1
            # -1 0
            # -1 -1
            # 0 -1
            #repeat for all points in grid (size x size)
            directions = [[1, -1], [1, 0], [1, 1], [0, 1],
                         [-1, 1], [-1, 0], [-1, -1], [0, -1]]

            grid = []
            for x in range(int(size/xstep)):
                for y in range(int(size/ystep)):
                    grid.append(str(x)+'x'+str(y))
            
            nullRow = '1,1,0,0,0,0,0,0,0,0'.split(',')      
     
            rowDict = {}
            for gridElement in grid:
                x, y = gridElement_to_x_y(gridElement)
                newRow = ['0', '0', x, y, xstep, ystep, 0, x*xstep + bottomLeftCorner.x, y*ystep + bottomLeftCorner.y, 0 + bottomLeftCorner.z]
                rowDict[gridElement] = newRow
            
            if self.bitMask.getNumOnBits() > 0:
                if self.scene is None:
                    self.scene = base.world

                removeList = []
                for key, value in rowDict.items():
                    collisions = 0
                    start = Vec3(value[-3], value[-2], value[-1])
                    for dir in directions:
                        end = Vec3((xstep*dir[0]) + start.x, (ystep*dir[1]) + start.y, start.z)

                        result = self.scene.rayTestClosest(start, end)

                        if result.hasHit():
                            collisions += 1

                    if collisions == 0:
                        removeList.append(key)

                for item in removeList:
                    rowDict.pop(item)
            
            for gridElement, row in rowDict.items():
                x, y = gridElement_to_x_y(gridElement)
                neighbours = []
                for direction in directions:
                    neighbourx = x - direction[0]
                    neighboury = y - direction[1]
                    neighbour = str(neighbourx)+'x'+str(neighboury)
                    if neighbour in grid:
                        neighbours.append(neighbour)
                    else:
                        neighbours.append('nope')
                filewriter.writerow(rowDict[gridElement])
                for n in neighbours:
                    if n in rowDict.keys():
                        newRow = rowDict[n].copy()
                        newRow[1] = 1
                    else:
                        newRow = nullRow.copy()
                    filewriter.writerow(newRow)
    
 

    

    
    
    
    