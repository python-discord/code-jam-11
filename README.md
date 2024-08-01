# EcoCord: A Discord Ecosystem Simulator

![EcoCord Logo](assets/readme/logo.png)

Welcome to EcoCord, an innovative Discord bot that transforms your server's activity into a living, breathing ecosystem! Created for the Python Code Jam 2024 with the theme of "Information Overload," EcoCord turns the constant stream of messages, reactions, and user interactions into a vibrant, visual representation of your community's digital life.

## What is EcoCord?

EcoCord is a unique Discord bot that creates a dynamic ecosystem based on your server's activity. It visualizes user interactions as various creatures in a simulated environment, bringing your community to life in a whole new way!

![EcoCord in Action](assets/readme/demo.gif)

### Key Features:

- **Real-time Ecosystem Visualization**: Watch as your server's activity is transformed into a lively ecosystem with birds, snakes, and frogs representing active users.
- **Activity-based Interactions**: The more active your server, the more vibrant and diverse the ecosystem becomes!
- **User Avatars**: See your community members represented as cute critters with their own avatars.
- **Word Clouds**: Popular topics and frequently used words appear as dynamic word clouds in the sky.
- **Reaction Emojis**: Watch as reaction emojis float across the screen, adding extra flair to your ecosystem.
- **GIF Generation**: Automatically generate and share GIFs of your server's ecosystem in action.

## How It Works

EcoCord listens to various events in your Discord server:

1. **Messages**: Each message spawns or activates a critter in the ecosystem.
2. **Reactions**: Emojis used in reactions appear and animate in the environment.
3. **Typing**: Users typing are represented by their critters becoming more active.

As these events occur, the ecosystem evolves:

- Critters move around, interact, and respond to the overall activity level.
- Word clouds form and dissipate based on message content.

### Critter Types

EcoCord features three main types of critters, each with unique behaviors and representations:

1. **Birds**:
   - Fly smoothly across the sky
   - Change direction randomly
   - Flap their wings as they move

2. **Snakes**:
   - Slither along the ground
   - Move in a sinusoidal pattern
   - Grow longer as they become more active

3. **Frogs**:
   - Hop around the lower part of the ecosystem
   - Have distinct rest and jump states
   - Scale in size based on their vertical position

Each critter type is designed to represent different aspects of user activity and add variety to the ecosystem visualization.

## Technical Challenges

EcoCord overcomes several technical challenges to create a seamless and engaging experience:

1. **GIF Generation and Multithreading**:
   - Utilizes a separate process for GIF generation to avoid blocking the main application
   - Implements a shared memory approach using `multiprocessing.Array` for efficient frame sharing between processes
   - Manages concurrent access to shared resources with locks and queues
   - Generates GIFs in under 1s on typical hardware

2. **SQLite Database Integration**:
   - Uses `aiosqlite` for asynchronous database operations
   - Stores and retrieves guild configurations and user information

3. **Efficient Rendering with Pygame**:
   - Optimizes drawing operations to handle multiple moving entities
   - Implements custom drawing algorithms for each critter type
   - Manages transparency and layering for complex visual effects
   - Parallax scrolling of background clouds to add depth to the ecosystem

4. **Discord API Integration**:
   - Handles real-time events from Discord using `discord.py`
   - Manages rate limits and connection issues gracefully
   - Implements command handling and permission checks for bot configuration

5. **Dynamic Word Cloud Generation**:
   - Processes message content in real-time to extract relevant words
   - Generates and updates word clouds based on frequently used terms
   - Integrates word clouds seamlessly into the ecosystem visualization with masking

6. **Avatar Integration and Image Processing**:
   - Fetches and processes user avatars from Discord
   - Applies masks and transformations to integrate avatars with critter designs
   - Handles various image formats and sizes efficiently

These technical solutions work together to create a responsive, visually appealing, and interactive ecosystem that accurately represents the activity in your Discord server.

## Connection to the Theme: Information Overload

EcoCord tackles the theme of "Information Overload" by:

1. **Visualizing Data**: Transforming the overwhelming stream of Discord messages and events into a visually appealing and easily digestible format.
2. **Aggregating Information**: Combining multiple data points (messages, reactions, user activity) into a single, coherent representation.
3. **Dynamic Adaptation**: The ecosystem evolves based on the volume and type of information, providing a real-time view of server activity.
4. **Filtering and Focusing**: By representing users as critters and popular topics as word clouds, EcoCord helps users focus on key information amidst the noise.

## Innovation Spotlight

EcoCord stands out in addressing "Information Overload" through its unique approach:

1. **Dynamic Visualization**: We transform raw data into an engaging, living ecosystem.
2. **Intelligent Aggregation**: Our algorithm combines multiple data points to create meaningful representations.
3. **Scalability**: EcoCord efficiently handles high-volume servers without performance degradation.

### Key Innovation: Efficient GIF Generation

Our multithreaded GIF generation process is a standout feature:

```python
@staticmethod
async def _gif_generation_process(
    shared_frames: SharedNumpyArray,
    current_frame_index: multiprocessing.Value,
    frame_count_queue: multiprocessing.Queue,
    gif_info_queue: multiprocessing.Queue,
    fps: int,
) -> None:
    frames = shared_frames.get_array()

    with ThreadPoolExecutor() as executor:
        while True:
            frame_count = frame_count_queue.get()
            if frame_count is None:
                break

            start_index = current_frame_index.value
            ordered_frames = np.roll(frames, -start_index, axis=0)

            frames = list(executor.map(Image.fromarray, ordered_frames))

            duration = int(1000 / fps)

            with io.BytesIO() as gif_buffer:
                optimized_frames[0].save(
                    gif_buffer,
                    format="GIF",
                    save_all=True,
                    append_images=frames[1:],
                    optimize=False,
                    duration=[duration] * (len(frames)),
                    loop=0,
                )

                gif_data = gif_buffer.getvalue()

            gif_info_queue.put((gif_data, time.time()))
```

This approach allows us to generate high-quality GIFs efficiently, even for servers with thousands of messages per minute. Key features include:

1. Asynchronous processing using `asyncio`
2. Shared memory for frame data using `SharedNumpyArray`
3. Multithreading for frame optimization
4. Efficient frame ordering and GIF creation

## Getting Started

### Prerequisites

- Python 3.12
- Poetry (for dependency management)
- A Discord Bot Token

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/ardent-andromedas/python-code-jam-2024.git
   cd ecocord
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Set up your environment variables:
   Create a `.env` file in the project root and add your Discord bot token:
   ```
   BOT_TOKEN=<YOUR BOT TOKEN>
   ```

### Running EcoCord

1. Start the bot:
   ```
   poetry run run
   ```

2. Invite the bot to your Discord server using the OAuth2 URL generated for your bot in the Discord Developer Portal.

The bot should be configured for a Guild Install, with the `applications.commands` and `bot` scopes, and `Attach Files`, `Create Public Threads`, `Embed Links`, `Read Message History`, `Send Messages`, `Send Messages in Threads`, `Use Slash Commands`, and `View Channels` permissions.

3. Use the `/configure` command in your server to set up the channels where EcoCord will operate.


## Configuration

To set up EcoCord in your server, use the `/configure` command. This command allows you to specify which channels the bot should monitor and where it should post ecosystem GIFs.

![Configure Command](assets/readme/configure.png)

The configuration options include:

- **Ecosystem Channel**: The channel where EcoCord will monitor activity and generate the ecosystem.
- **GIF Channel**: The channel where EcoCord will post generated GIFs of the ecosystem.

After running the `/configure` command, follow the prompts to select the appropriate channels. EcoCord will then start monitoring the specified ecosystem channel and post GIFs in the designated GIF channel.


## Usage

Once EcoCord is running in your server, it will automatically start creating and updating the ecosystem based on server activity. Here are some key commands and features:

- `/configure`: Set up the channels where EcoCord will operate and where GIFs will be posted.
- Activity Visualization: Watch the ecosystem change in real-time as your server becomes more or less active.
- GIF Generation: Periodically, EcoCord will generate and post GIFs of the ecosystem in threads in the designated channel.

## Contributing

We welcome contributions to EcoCord! If you have ideas for new features, improvements, or bug fixes, please feel free to:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Thanks to the Python Discord community for organizing the Python Code Jam 2024
- Shoutout to all the contributors who helped bring EcoCord to life
- Special thanks to the creators of the wonderful libraries used in this project, including Discord.py, Pygame, and Pillow

### Our team

All team members contributed to the initial project planning and ideation. Special thanks to:

[Stovoy](https://github.com/Stovoy)
* Project lead and primary developer
* Conceived the ecosystem concept and implemented the core functionality
* Contributed the majority of the codebase

[Jaavv](https://github.com/Jaavv)
* Contributed to early development stages
* Implemented initial versions of the Discord bot and SQLite integration

[Walkercito](https://github.com/Walkercito)
* Provided valuable testing support
* Sourced the cloud assets used in the background from [Free Sky with Clouds Background Pixel Art Set](https://free-game-assets.itch.io/free-sky-with-clouds-background-pixel-art-set)

[ShadowDogger](https://github.com/ShadowDogger) and [tinoy-t](https://github.com/tinoy-t)
* Participated in brainstorming sessions
* Offered insights and suggestions during the planning phase

While some initially planned features like backfilling, timelapses, and snapshotting were ultimately not implemented, the team's collaborative efforts in the early stages helped shape the project's direction and scope.