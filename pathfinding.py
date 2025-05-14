from collections import deque
import heapq

def bfs(start, goal, is_valid):
    queue = deque([start])
    visited = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break

        for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor not in visited and is_valid(*neighbor):
                queue.append(neighbor)
                visited[neighbor] = current

    path = []
    current = goal
    while current and current in visited:
        path.append(current)
        current = visited[current]
    return path[::-1] if path and path[0] == start else []

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(start, goal, is_valid):
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start))
    came_from = {}
    cost_so_far = {start: 0}

    while open_set:
        _, cost, current = heapq.heappop(open_set)

        if current == goal:
            break

        for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if not is_valid(*neighbor):
                continue
            new_cost = cost_so_far[current] + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(neighbor, goal)
                heapq.heappush(open_set, (priority, new_cost, neighbor))
                came_from[neighbor] = current

    path = []
    current = goal
    while current and current in came_from:
        path.append(current)
        current = came_from[current]
    return path[::-1] if path and path[0] == start else []
