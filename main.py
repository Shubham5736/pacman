# /// script
# dependencies = [
#     "pygame-ce",
# ]
# ///

import asyncio
import pygame

from game.game import Game


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())