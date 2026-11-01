
"""Collision detection between Pac-Man and ghosts."""


def check_collision(player, ghost):
    """
    Check whether Pac-Man and a ghost are touching.

    Both entities use pixel coordinates relative to the maze.
    """

    if not ghost.alive:
        return False

    dx = player.x - ghost.x
    dy = player.y - ghost.y

    collision_distance = player.radius + ghost.radius

    distance_squared = dx * dx + dy * dy

    return distance_squared <= collision_distance * collision_distance


def check_ghost_collisions(player, ghosts):
    """
    Return a list of ghosts currently touching Pac-Man.
    """

    colliding_ghosts = []

    for ghost in ghosts:
        if check_collision(player, ghost):
            colliding_ghosts.append(ghost)

    return colliding_ghosts


"""
We use the distance between the centres of Pac-Man and a ghost:

            d^2=(x_1-x_2)^2+(y_1-y_2)^2

A collision occurs when:

            d <= radius_player + radius_ghost


"""