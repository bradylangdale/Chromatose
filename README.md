
![Chromatose](/Assets/assets/Text/ChromatoseLight.png)

## Introduction
Chromatose is a first-person shooter where your goal is to survive as long as possible but with a twist. As hinted by in the name the environment around changes colors according to your characters status.

## Rules
You start with half of each color, shown by the bars in the bottom left corner. These colors correspond to your attributes:
- Red is health, don't let it drop down or the game is over
- Green is ammo, you need this to kill the enemies
- Blue is shield, this is a great way to fling enemies far away from the player to get some personal space

Your job is to kill as many enemies as possible, every time you kill one, it will drop a crystal that you can use to replenish that color. 

The game's enemy count and damage scales as your score increases, How long can you survive?

## How to Run the Code
Chromatose is made using [Panda3D](https://www.panda3d.org/). So you'll first need to [install](https://docs.panda3d.org/1.10/python/introduction/installation-windows) the SDK to get started. From there you can choose to either use your own Python installation or use Panda3D's `ppython` either will work, but be sure to install the binding for the Python version your using if you choose that route. We've also provided a `requirement.txt` with all of our dependencies to run the code. 

## Building a `.exe` From The Code
Once the project builds and runs fine of your machine including changes you may have made, you can export the game as a single `.exe`. We used PyInstaller to accomplished this through the [`auto-py-to-exe`](https://pypi.org/project/auto-py-to-exe/) tool. First select the main script from the game. Then add you assets folder. Finally, add Panda3D's `/bin`, `/direct`, `/panda3d`, and the folder containing all the Panda3D's files. You'll also need to add the Panda3D files to `--path` under the "Advanced" tab. Additionally, you can select an icon for the game and splash screen, however these aren't necessary. Once all the settings are you configured you can now build the game and get a single portable `.exe`.

## Release Version
If you don't want to go through setting up Panda3D and just want to play the game. We've built and provided a single `.exe` [release](https://github.com/bradylangdale/Chromatose/releases/tag/release) for you!

# Game Design

## States
Chromatose has four main states, `Start Menu`, `Pause`, `Playing`, and `Retry`. The `Start Menu` state simple display a UI with the games controls and descriptions along with a play button. The `Pause` state allows the game to be paused, `Retry` also builds off all this can includes some additionally logic to clear the scene. Finally, `Playing` enables physics, controls, and enemy logic.

## UI
The 2D graphical interface of Chromatrose largely makes use of Panda3D's built in `DirectGUI` framework. We've included a font and some rendered images like the logo.

## Physics
A large part of what makes any 3D game fun is physics. It allows the user to interact with the environment in a very organic way and we've tried to use it where ever possible rather than using kinematics. Panda3D's provides a few options for the backend physics engine used but we chose Bullet as it is widely used and well documented. However, letting physics do a bunch of stuff for you can lead to some silly bugs, but it makes mechanics like the shield very cool.

## Rendering
Because we wanted to manipulate the colors of all objects in the scene at runtime we made use of Panda3D's auto shader functions. This allows us to manipulate coloring at runtime without needing to make our own shaders mean all the game code is still pure Python. We also wanted to leverage emission maps, normals maps, and transparency to really make colors pop. This combined with bloom creates some really cool effects when gaining and loosing, health, ammo, and shield. To do this we had to use a Physically Based Renderer (PBR), luckily Panda3D has this as a Third Party package called `simplepbr`. Unfornately, this initially clashed with the built in shaderrs Panda3D provided, so too make the two work together we had modified the `Pipeline` class of `simplepbr` to allow Panda3D and it to use the same `FilterManager`. Basically, this allows both of them to control shaders in the scene. This can lead to some unexpected problems like certain functions in Panda3D not working as expected, but we were aware of this during development and worked around to maintain the pure Python status of the project. The result is nice renders using PBR and post-processing without ever needing to write a shader.
